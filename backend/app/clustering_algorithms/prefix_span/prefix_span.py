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



# Each entry: SQL query and the column that holds the event label.
# The query MUST return columns: patient_id, <item_column>, event_date
SEQUENCE_QUERIES = {
    "conditions": {
        "query": """
            SELECT patient_id, description AS item, start_date AS event_date
            FROM condition
            ORDER BY patient_id, start_date
        """,
    },
    "encounters": {
        "query": """
            SELECT patient_id, encounter_class AS item, start_date AS event_date
            FROM encounter
            ORDER BY patient_id, start_date
        """,
    },
    "medications": {
        "query": """
            SELECT patient_id, description AS item, start_date AS event_date
            FROM medication
            ORDER BY patient_id, start_date
        """,
    },
    "multi_event": {
        "query": """
            SELECT patient_id, 'C:' || description AS item, start_date AS event_date
            FROM condition
            UNION ALL
            SELECT patient_id, 'E:' || encounter_class AS item, start_date AS event_date
            FROM encounter
            UNION ALL
            SELECT patient_id, 'M:' || description AS item, start_date AS event_date
            FROM medication
            ORDER BY patient_id, event_date
        """,
    },
}


def _remove_consecutive_duplicates(items: list[str]) -> list[str]:
    """[A, A, B, B, A] -> [A, B, A]"""
    if not items:
        return items
    result = [items[0]]
    for item in items[1:]:
        if item != result[-1]:
            result.append(item)
    return result


def build_sequences(engine, sequence_type: str) -> dict[str, list[str]]:
    """Load events from DB and return {patient_id: [event, event, ...]}."""
    if sequence_type not in SEQUENCE_QUERIES:
        raise ValueError(
            f"Unknown sequence_type '{sequence_type}'. "
            f"Choose from {list(SEQUENCE_QUERIES.keys())}"
        )

    df = pd.read_sql(text(SEQUENCE_QUERIES[sequence_type]["query"]), con=engine)

    sequences: dict[str, list[str]] = {}
    for patient_id, group in df.groupby("patient_id", sort=False):
        sequences[str(patient_id)] = _remove_consecutive_duplicates(
            group["item"].tolist()
        )
    return sequences



def _is_subsequence(short: list[str], long: list[str]) -> bool:
    """Check if `short` is a subsequence of `long` (not necessarily contiguous)."""
    it = iter(long)
    return all(item in it for item in short)


class PrefixSpan:
    """
    PrefixSpan sequential pattern mining.

    Parameters
    ----------
    min_support : float
        Minimum support as a fraction of total sequences (0.0 - 1.0).
    max_length : int
        Maximum pattern length to mine.
    closed_only : bool
        If True, keep only closed patterns — patterns where no supersequence
        has the same support count.
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

        initial_projections = [(i, 0) for i in range(len(sequences))]
        self._grow(prefix=[], projected_db=initial_projections, sequences=sequences)

        if self.closed_only:
            self._filter_closed()

        self.frequent_patterns.sort(key=lambda x: (-x[1], len(x[0])))
        return self

    def get_results(self) -> list[dict]:
        return [
            {
                "pattern": pattern,
                "length": len(pattern),
                "support_count": count,
                "support_fraction": round(count / self.n_sequences, 4),
            }
            for pattern, count in self.frequent_patterns
        ]


    def _grow(
        self,
        prefix: list[str],
        projected_db: list[tuple[int, int]],
        sequences: list[list[str]],
    ):
        """Recursively extend `prefix` with frequent items from `projected_db`."""
        if len(prefix) >= self.max_length:
            return
        if len(projected_db) < self._min_count:
            return

        # For each item that can follow the current prefix, collect the
        # projected database entries (sequence index + position after the item).
        next_item_projections: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for seq_idx, start_pos in projected_db:
            seq = sequences[seq_idx]
            seen: set[str] = set()
            for pos in range(start_pos, len(seq)):
                item = seq[pos]
                if item not in seen:
                    seen.add(item)
                    next_item_projections[item].append((seq_idx, pos + 1))

        # Recurse into every frequent extension
        for item, new_projected_db in next_item_projections.items():
            support = len(new_projected_db)
            if support < self._min_count:
                continue

            new_prefix = prefix + [item]
            self.frequent_patterns.append((new_prefix, support))
            self._grow(new_prefix, new_projected_db, sequences)

    def _filter_closed(self):
        """
        Keep only closed patterns. A pattern P is closed if no longer pattern
        (supersequence) has the exact same support count.

        Because PrefixSpan builds patterns by prefix extension, every generated
        pattern is a prefix of its children. We check both prefix relationships
        (fast) and true subsequence relationships for same-support patterns.
        """
        by_support: dict[int, list[list[str]]] = defaultdict(list)
        for pattern, support in self.frequent_patterns:
            by_support[support].append(pattern)

        closed: list[tuple[list[str], int]] = []
        for pattern, support in self.frequent_patterns:
            is_closed = True
            for longer in by_support[support]:
                if len(longer) > len(pattern) and _is_subsequence(pattern, longer):
                    is_closed = False
                    break
            if is_closed:
                closed.append((pattern, support))

        self.frequent_patterns = closed



def run_prefix_span(
    engine,
    sequence_type: str = "conditions",
    min_support: float = 0.05,
    max_length: int = 5,
    closed_only: bool = True,
) -> dict:
    """Run PrefixSpan mining end-to-end and return results dict."""
    print(f"Building {sequence_type} sequences...")
    patient_sequences = build_sequences(engine, sequence_type)
    sequence_list = list(patient_sequences.values())
    avg_len = sum(len(s) for s in sequence_list) / max(len(sequence_list), 1)
    print(f"  {len(sequence_list)} patients, avg sequence length {avg_len:.1f}")

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

    for seq_type in ["conditions", "encounters", "medications"]:
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

        print(f"\nTop 20 patterns (out of {result['n_patterns']}):")
        for p in result["patterns"][:20]:
            pct = p["support_fraction"] * 100
            print(f"  [{p['length']}] {' -> '.join(p['pattern'])}  ({p['support_count']} patients, {pct:.1f}%)")

        db = SessionLocal()
        try:
            run_id = save_sequence_results(db, result)
            print(f"\nSaved to database: run_id={run_id}")
        finally:
            db.close()
