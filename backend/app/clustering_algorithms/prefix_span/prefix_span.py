"""Mine frequent clinical-event sequences with PrefixSpan and persist them for the API.

Run from `backend/app/` (same convention as k_prototypes.py):
    python clustering_algorithms/prefix_span/prefix_span.py

Output tables:
  - prefix_span_pattern          (one row per mined pattern)
  - prefix_span_patient_pattern  (which patients contain each pattern)

Pattern string format (agreed with the frontend parser `parsePattern.ts`):
  "PREFIX:Value -> PREFIX:Value -> PREFIX:Value"

Prefixes are the four the API/FE already colour-codes:
  C  = Condition,  M = Medication,  P = Procedure,  CP = CarePlan.

Same-day event grouping with parentheses is supported by the FE parser but the
`prefixspan` PyPI library mines over a flat list-of-items (no itemset support),
so we flatten each patient's timeline chronologically and let the library treat
every event as its own step. This maximises support and keeps the mined items
readable without bloating the item vocabulary.
"""

import os
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine, SessionLocal  # provided by backend/app/db/__init__.py
from save_results import save_prefix_span_results


# ------------------------ tunables ---------------------------------------------------

# Lower bound on how many patients must share a pattern before it is worth keeping.
# Expressed as a fraction of the patient count; the absolute minsup is derived at runtime.
MIN_SUPPORT_PCT = 0.06  # 6% of patients — raised from 3% for speed

# Shortest mined pattern we persist. 1-event "patterns" are trivial.
MIN_PATTERN_LENGTH = 2

# Longest pattern the miner is allowed to emit — caps combinatorial blow-up on dense timelines.
MAX_PATTERN_LENGTH = 5  # lowered from 7 for speed

# Cap per-patient timeline length (most recent events kept). Long Synthea histories otherwise
# dominate the projected databases and inflate runtime without adding pattern signal.
MAX_EVENTS_PER_PATIENT = 80  # lowered from 250 for speed

# Final number of patterns to persist and print.
TOP_K = 100

# Rolling window (days) applied per patient. Only events within this span before the
# patient's most recent event are included — keeps sequences temporally coherent and
# dramatically shrinks the projected databases for long histories.
WINDOW_DAYS = 365  # 1 year


# ------------------------ data loading -----------------------------------------------

@dataclass(frozen=True)
class Event:
    patient_id: str
    date: pd.Timestamp
    item: str  # already prefixed, e.g. "C:Hypertension"


def _load_events(engine) -> pd.DataFrame:
    """Pull every clinical event we sequence over, tagged with its prefix."""
    # All four queries produce (patient_id, date, description) — we prefix `description`
    # in Python and concat. The union could be done in SQL but splitting keeps each query
    # simple and debuggable.
    queries = {
        "C": text("""
            SELECT patient_id, start_date AS event_date, description
            FROM condition
            WHERE description IS NOT NULL AND start_date IS NOT NULL
        """),
        "M": text("""
            SELECT patient_id, start_date AS event_date, description
            FROM medication
            WHERE description IS NOT NULL AND start_date IS NOT NULL
        """),
        "P": text("""
            SELECT patient_id, start_date AS event_date, description
            FROM "procedure"
            WHERE description IS NOT NULL AND start_date IS NOT NULL
        """),
        "CP": text("""
            SELECT patient_id, start_date AS event_date, description
            FROM careplan
            WHERE description IS NOT NULL AND start_date IS NOT NULL
        """),
    }

    frames = []
    for prefix, q in queries.items():
        print(f"  Querying {prefix} events...")
        df = pd.read_sql(q, con=engine)
        if df.empty:
            print(f"    (no rows)")
            continue
        df["item"] = prefix + ":" + df["description"].astype(str).str.strip()
        print(f"    {len(df):,} rows, {df['patient_id'].nunique():,} patients")
        frames.append(df[["patient_id", "event_date", "item"]])

    if not frames:
        return pd.DataFrame(columns=["patient_id", "event_date", "item"])

    all_events = pd.concat(frames, ignore_index=True)
    all_events["event_date"] = pd.to_datetime(all_events["event_date"])
    return all_events


# ------------------------ sequence construction --------------------------------------

# Deterministic ordering for same-day events so the miner sees the same sequence across runs.
_PREFIX_ORDER = {"C": 0, "M": 1, "P": 2, "CP": 3}


def _prefix_rank(item: str) -> int:
    prefix = item.split(":", 1)[0]
    return _PREFIX_ORDER.get(prefix, 99)


def build_sequences(engine) -> tuple[list[list[str]], list[str]]:
    """Return (sequences, patient_ids) aligned by position.

    Each sequence is a chronologically ordered list of prefixed item strings for one patient.
    Duplicate consecutive items (same item reported multiple times on the same day) are
    collapsed so trivial repetitions don't inflate pattern support.
    """
    events = _load_events(engine)
    if events.empty:
        return [], []

    # Sort once: patient, then time, then deterministic prefix/item tie-breakers.
    events["_pref_rank"] = events["item"].map(_prefix_rank)
    events = events.sort_values(
        ["patient_id", "event_date", "_pref_rank", "item"],
        kind="mergesort",
    )

    sequences: list[list[str]] = []
    patient_ids: list[str] = []
    all_pids = list(events.groupby("patient_id", sort=False).groups.keys())
    total = len(all_pids)
    print(f"  Building sequences for {total:,} patients (1-year window)...")
    window = pd.Timedelta(days=WINDOW_DAYS)
    for i, (pid, group) in enumerate(events.groupby("patient_id", sort=False), start=1):
        # Restrict to events within 1 year of the patient's most recent event.
        cutoff = group["event_date"].max() - window
        group = group[group["event_date"] >= cutoff]
        seq = group["item"].tolist()
        # Collapse runs of identical items (e.g. same med re-prescribed daily) to a single step.
        deduped: list[str] = []
        for it in seq:
            if not deduped or deduped[-1] != it:
                deduped.append(it)
        if len(deduped) > MAX_EVENTS_PER_PATIENT:
            deduped = deduped[-MAX_EVENTS_PER_PATIENT:]  # keep most recent window
        if deduped:
            sequences.append(deduped)
            patient_ids.append(str(pid))
        if i % 5000 == 0 or i == total:
            print(f"    {i:,}/{total:,} patients processed")

    return sequences, patient_ids


# ------------------------ mining + patient attribution -------------------------------

def _is_subsequence(pattern: list[str], sequence: list[str]) -> bool:
    """Two-pointer check: is `pattern` a (non-contiguous) subsequence of `sequence`?"""
    it = iter(sequence)
    return all(any(item == p for item in it) for p in pattern)


def mine_patterns(
    sequences: list[list[str]],
    min_support_pct: float = MIN_SUPPORT_PCT,
    min_pattern_length: int = MIN_PATTERN_LENGTH,
    max_pattern_length: int = MAX_PATTERN_LENGTH,
    top_k: int = TOP_K,
) -> list[tuple[int, list[str]]]:
    """Run PrefixSpan and return [(support_count, pattern_items), ...] sorted by rank."""
    if not sequences:
        return []

    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * min_support_pct))

    ps = PrefixSpan(sequences)
    ps.minlen = min_pattern_length
    ps.maxlen = max_pattern_length

    # Mine ALL patterns meeting abs_minsup so the same-type-consecutive filter has the
    # full population to work with — topk would miss diverse cross-type patterns that
    # rank below the P->P-dominated top.
    print(f"  Running PrefixSpan (n={n_patients:,}, abs_minsup={abs_minsup}, minlen={min_pattern_length}, maxlen={max_pattern_length})...")
    mined: list[tuple[int, list[str]]] = ps.frequent(abs_minsup)
    print(f"  PrefixSpan returned {len(mined)} patterns (before filtering)")

    # Enforce minlen and minsup defensively.
    filtered_length = []
    for sup, pat in mined:
        if len(pat) >= min_pattern_length and sup >= abs_minsup:
            filtered_length.append((sup, pat))
    mined = filtered_length

    # Drop patterns where any two consecutive items share the same event-type prefix
    # (e.g. P:Appendectomy -> P:Colonoscopy is disallowed).
    filtered_type = []
    for sup, pat in mined:
        has_same_type = False
        for i in range(len(pat) - 1):
            type_a = pat[i].split(":")[0]
            type_b = pat[i + 1].split(":")[0]
            if type_a == type_b:
                has_same_type = True
                break
        if not has_same_type:
            filtered_type.append((sup, pat))
    mined = filtered_type
    print(f"  {len(mined)} patterns after same-type-consecutive filter")

    # Sort by support descending and keep the top_k survivors.
    # Tuples sort by their first element by default, so (support, pattern) sorts by support.
    mined.sort(reverse=True)
    mined = mined[:top_k]

    print(f"\n--- Top {len(mined)} patterns ---")
    for rank, (sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        print(f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] {pattern_to_str(pat)}")
    print("--- end of pattern list ---\n")

    # Support-sorted DESC; rank ordering follows position.
    return mined


def attribute_patients(
    mined: list[tuple[int, list[str]]],
    sequences: list[list[str]],
    patient_ids: list[str],
) -> dict[int, list[str]]:
    """For each mined pattern (keyed by rank = 1..N), list patients whose sequence contains it."""
    memberships: dict[int, list[str]] = {}
    total = len(mined)
    for rank, (_support, pattern) in enumerate(mined, start=1):
        contained = [
            patient_ids[i]
            for i, seq in enumerate(sequences)
            if _is_subsequence(pattern, seq)
        ]
        memberships[rank] = contained
        if rank % 20 == 0 or rank == total:
            print(f"  Attributed {rank}/{total} patterns (last: {len(contained)} patients matched)")
    return memberships


def pattern_to_str(pattern: Iterable[str]) -> str:
    return " -> ".join(pattern)


# ------------------------ orchestrator -----------------------------------------------

def run(engine, db_session) -> None:
    print("Loading clinical events...")
    sequences, patient_ids = build_sequences(engine)
    n_patients = len(sequences)
    print(f"  {n_patients} patients with at least one event")
    if n_patients == 0:
        print("  nothing to mine — aborting")
        return

    avg_len = sum(len(s) for s in sequences) / n_patients
    print(f"  avg sequence length: {avg_len:.1f}")

    print(f"Mining patterns (min_support={MIN_SUPPORT_PCT:.0%}, top_k={TOP_K})...")
    mined = mine_patterns(sequences)
    print(f"  {len(mined)} patterns kept after filtering")
    if not mined:
        print("  no patterns met thresholds — aborting write")
        return

    print("Resolving patient memberships...")
    memberships = attribute_patients(mined, sequences, patient_ids)

    rows: list[dict] = []
    for rank, (support, pattern) in enumerate(mined, start=1):
        rows.append({
            "rank": rank,
            "pattern_str": pattern_to_str(pattern),
            "length": len(pattern),
            "support_count": int(support),
            "support_pct": round(100.0 * support / n_patients, 2),
        })

    print("Writing to database...")
    save_prefix_span_results(db_session, rows, memberships)


if __name__ == "__main__":
    load_dotenv()
    with SessionLocal() as db:
        run(engine, db)
