"""
PrefixSpan sequential pattern mining on patient medical event histories.

Builds per-patient sequences of medical events (conditions, encounters,
medications) ordered chronologically, then discovers frequent subsequences
using the PrefixSpan algorithm.

Run standalone:
    cd backend/app/clustering_algorithms/prefix_span
    python prefix_span.py
"""

from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Data extraction — one sequence per patient
# ---------------------------------------------------------------------------

def _deduplicate_consecutive(items: list[str]) -> list[str]:
    """Remove consecutive duplicate items from a list."""
    if not items:
        return items
    return [items[0]] + [items[i] for i in range(1, len(items)) if items[i] != items[i - 1]]


def build_condition_sequences(engine) -> dict[str, list[str]]:
    """Each patient -> ordered list of condition descriptions."""
    df = pd.read_sql(
        text("""
            SELECT patient_id, description, start_date
            FROM condition
            ORDER BY patient_id, start_date
        """),
        con=engine,
    )
    sequences: dict[str, list[str]] = {}
    for pid, group in df.groupby("patient_id", sort=False):
        sequences[str(pid)] = _deduplicate_consecutive(group["description"].tolist())
    return sequences


def build_encounter_sequences(engine) -> dict[str, list[str]]:
    """Each patient -> ordered list of encounter classes."""
    df = pd.read_sql(
        text("""
            SELECT patient_id, encounter_class, start_date
            FROM encounter
            ORDER BY patient_id, start_date
        """),
        con=engine,
    )
    sequences: dict[str, list[str]] = {}
    for pid, group in df.groupby("patient_id", sort=False):
        sequences[str(pid)] = _deduplicate_consecutive(group["encounter_class"].tolist())
    return sequences


def build_medication_sequences(engine) -> dict[str, list[str]]:
    """Each patient -> ordered list of medication descriptions."""
    df = pd.read_sql(
        text("""
            SELECT patient_id, description, start_date
            FROM medication
            ORDER BY patient_id, start_date
        """),
        con=engine,
    )
    sequences: dict[str, list[str]] = {}
    for pid, group in df.groupby("patient_id", sort=False):
        sequences[str(pid)] = _deduplicate_consecutive(group["description"].tolist())
    return sequences


def build_multi_event_sequences(engine) -> dict[str, list[str]]:
    """
    Each patient -> ordered list of tagged events mixing conditions,
    encounters, and medications.  Tags: 'C:', 'E:', 'M:'.
    """
    df = pd.read_sql(
        text("""
            SELECT patient_id, 'C:' || description AS item, start_date AS event_date
            FROM condition
            UNION ALL
            SELECT patient_id, 'E:' || encounter_class AS item, start_date AS event_date
            FROM encounter
            UNION ALL
            SELECT patient_id, 'M:' || description AS item, start_date AS event_date
            FROM medication
            ORDER BY patient_id, event_date
        """),
        con=engine,
    )
    sequences: dict[str, list[str]] = {}
    for pid, group in df.groupby("patient_id", sort=False):
        sequences[str(pid)] = _deduplicate_consecutive(group["item"].tolist())
    return sequences


BUILDERS = {
    "conditions": build_condition_sequences,
    "encounters": build_encounter_sequences,
    "medications": build_medication_sequences,
    "multi_event": build_multi_event_sequences,
}


# ---------------------------------------------------------------------------
# PrefixSpan algorithm
# ---------------------------------------------------------------------------

class PrefixSpan:
    """
    PrefixSpan sequential pattern mining.

    Parameters
    ----------
    min_support : float
        Minimum support as a fraction of total sequences (0.0-1.0).
    max_length : int
        Maximum pattern length to mine.
    closed_only : bool
        If True, only return closed patterns (no supersequence with the
        same support count). Dramatically reduces noise.
    """

    def __init__(
        self,
        min_support: float = 0.05,
        max_length: int = 5,
        closed_only: bool = True,
    ):
        self.min_support = min_support
        self.max_length = max_length
        self.closed_only = closed_only
        self.n_sequences = 0
        self._min_count = 0
        self.frequent_patterns: list[tuple[list[str], int]] = []

    def fit(self, sequences: list[list[str]]) -> "PrefixSpan":
        self.n_sequences = len(sequences)
        self._min_count = max(1, int(self.min_support * self.n_sequences))
        self.frequent_patterns = []

        projected_db = [(i, 0) for i in range(len(sequences))]
        self._mine([], projected_db, sequences)

        if self.closed_only:
            self._filter_closed()

        self.frequent_patterns.sort(key=lambda x: (-x[1], len(x[0])))
        return self

    def _mine(
        self,
        prefix: list[str],
        projected_db: list[tuple[int, int]],
        sequences: list[list[str]],
    ):
        if len(prefix) >= self.max_length:
            return

        # early exit: projected DB already smaller than min_count
        if len(projected_db) < self._min_count:
            return

        # count frequency of each item that can extend the prefix
        item_counts: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for seq_idx, start_pos in projected_db:
            seq = sequences[seq_idx]
            seen_items: set[str] = set()
            for pos in range(start_pos, len(seq)):
                item = seq[pos]
                if item not in seen_items:
                    seen_items.add(item)
                    item_counts[item].append((seq_idx, pos + 1))

        for item, new_projected in item_counts.items():
            support = len(new_projected)
            if support < self._min_count:
                continue

            new_prefix = prefix + [item]
            self.frequent_patterns.append((new_prefix, support))
            self._mine(new_prefix, new_projected, sequences)

    def _filter_closed(self):
        """
        Remove non-closed patterns. A pattern P is closed if no
        supersequence of P has the same support count.

        A pattern Q is a supersequence of P if P is a contiguous prefix
        of Q (since PrefixSpan only extends prefixes, we only need to
        check prefix relationships).
        """
        # index patterns by support count for fast lookup
        by_support: dict[int, list[list[str]]] = defaultdict(list)
        for pattern, support in self.frequent_patterns:
            by_support[support].append(pattern)

        closed = []
        for pattern, support in self.frequent_patterns:
            # check if any longer pattern with the same support is a
            # super-pattern (i.e. this pattern is a prefix of it)
            is_closed = True
            for candidate in by_support[support]:
                if len(candidate) > len(pattern) and candidate[: len(pattern)] == pattern:
                    is_closed = False
                    break
            if is_closed:
                closed.append((pattern, support))

        self.frequent_patterns = closed

    def get_results(self) -> list[dict]:
        """Return patterns as a list of dicts with support fraction."""
        return [
            {
                "pattern": pattern,
                "length": len(pattern),
                "support_count": count,
                "support_fraction": round(count / self.n_sequences, 4),
            }
            for pattern, count in self.frequent_patterns
        ]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_prefix_span(
    engine,
    sequence_type: str = "conditions",
    min_support: float = 0.05,
    max_length: int = 5,
    closed_only: bool = True,
) -> dict:
    """
    Run PrefixSpan mining end-to-end.

    Returns a dict with run metadata and discovered patterns.
    """
    if sequence_type not in BUILDERS:
        raise ValueError(f"Unknown sequence_type '{sequence_type}'. Choose from {list(BUILDERS.keys())}")

    print(f"Building {sequence_type} sequences...")
    patient_sequences = BUILDERS[sequence_type](engine)
    sequence_list = list(patient_sequences.values())

    print(f"  {len(sequence_list)} patients, avg sequence length {sum(len(s) for s in sequence_list) / max(len(sequence_list), 1):.1f}")

    print(f"Running PrefixSpan (min_support={min_support}, max_length={max_length}, closed_only={closed_only})...")
    miner = PrefixSpan(min_support=min_support, max_length=max_length, closed_only=closed_only)
    miner.fit(sequence_list)

    patterns = miner.get_results()
    print(f"  Found {len(patterns)} frequent patterns")

    lengths = [len(s) for s in sequence_list]
    length_stats = {
        "min": int(min(lengths)) if lengths else 0,
        "max": int(max(lengths)) if lengths else 0,
        "mean": round(sum(lengths) / max(len(lengths), 1), 2),
        "median": int(sorted(lengths)[len(lengths) // 2]) if lengths else 0,
    }

    return {
        "sequence_type": sequence_type,
        "n_patients": len(sequence_list),
        "min_support": min_support,
        "max_length": max_length,
        "closed_only": closed_only,
        "n_patterns": len(patterns),
        "sequence_length_stats": length_stats,
        "patterns": patterns,
    }


if __name__ == "__main__":
    load_dotenv()

    from db import engine as db_engine
    from db.db_connector import SessionLocal
    from save_results import save_sequence_results

    sequence_types_to_run = ["conditions", "encounters", "medications"]

    for seq_type in sequence_types_to_run:
        print(f"\n{'=' * 60}")
        print(f"  SEQUENCE MINING: {seq_type.upper()}")
        print(f"{'=' * 60}")

        result = run_prefix_span(
            engine=db_engine,
            sequence_type=seq_type,
            min_support=0.05,
            max_length=5,
            closed_only=True,
        )

        # print top patterns
        print(f"\nTop 20 patterns (out of {result['n_patterns']}):")
        for p in result["patterns"][:20]:
            pct = p["support_fraction"] * 100
            print(f"  [{p['length']}] {' -> '.join(p['pattern'])}  ({p['support_count']} patients, {pct:.1f}%)")

        # save to database
        db = SessionLocal()
        try:
            run_id = save_sequence_results(db, result)
            print(f"\nSaved to database: run_id={run_id}")
        finally:
            db.close()
