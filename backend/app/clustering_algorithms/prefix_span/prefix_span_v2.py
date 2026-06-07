"""
PrefixSpan v2 - v1 + mining configuration.

Adds on top of v1:
  - overmine TOP_K * OVERMINE_MULTIPLIER patterns instead of just TOP_K
  - request closed patterns (closed=True): no superset with the same support
  - select the final TOP_K by support from the closed pool

No scoring or diversification yet - that's v3/v4.

Run from backend/:
    python app/clustering_algorithms/prefix_span/prefix_span_v2.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # backend/app/

from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine


MIN_SUPPORT_PCT = 0.01
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

OVERMINE_MULTIPLIER = 20  # NEW in v2

ITEM_BLACKLIST_SUBSTRINGS: frozenset[str] = frozenset({
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
})

_PREFIX_ORDER = {"C": 0, "M": 1, "P": 2, "CP": 3}


def load_events(engine) -> pd.DataFrame:
    query = text("""
        SELECT patient_id, start_date AS event_date,
               'C:'  || TRIM(description) AS item
        FROM condition
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'M:'  || TRIM(description)
        FROM medication
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'P:'  || TRIM(description)
        FROM "procedure"
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'CP:' || TRIM(description)
        FROM careplan
        WHERE description IS NOT NULL AND start_date IS NOT NULL
    """)
    df = pd.read_sql(query, con=engine)
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df


def build_sequences(engine) -> list[list[str]]:
    events = load_events(engine)

    events["_pref"] = events["item"].str.split(":", n=1).str[0]
    events["_pref_rank"] = events["_pref"].map(_PREFIX_ORDER).fillna(99).astype(int)
    events = events.sort_values(
        ["patient_id", "event_date", "_pref_rank", "item"],
        kind="mergesort",
    )

    item_lower = events["item"].str.lower()
    blacklist_mask = pd.Series(False, index=events.index)
    for sub in ITEM_BLACKLIST_SUBSTRINGS:
        blacklist_mask |= item_lower.str.contains(sub, regex=False)
    events = events[~blacklist_mask]

    maxd = events.groupby("patient_id", sort=False)["event_date"].transform("max")
    cutoff = maxd - pd.Timedelta(days=WINDOW_DAYS)
    events = events[events["event_date"] >= cutoff]

    same_pid = events["patient_id"].eq(events["patient_id"].shift())
    same_item = events["item"].eq(events["item"].shift())
    events = events[~(same_pid & same_item)]

    events = events.groupby("patient_id", sort=False, group_keys=False).tail(
        MAX_EVENTS_PER_PATIENT
    )

    grouped = events.groupby("patient_id", sort=False)["item"].apply(list)
    return grouped.tolist()


def encode(sequences: list[list[str]]) -> tuple[list[list[int]], list[str]]:
    vocab: dict[str, int] = {}
    inv: list[str] = []
    encoded: list[list[int]] = []
    for seq in sequences:
        out = []
        for it in seq:
            idx = vocab.get(it)
            if idx is None:
                idx = len(inv)
                vocab[it] = idx
                inv.append(it)
            out.append(idx)
        encoded.append(out)
    return encoded, inv


def pattern_to_str(pattern: Iterable[str]) -> str:
    return " -> ".join(pattern)


def mine(sequences: list[list[str]]) -> list[tuple[int, list[str]]]:
    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))

    int_seqs, inv_vocab = encode(sequences)

    ps = PrefixSpan(int_seqs)
    ps.minlen = MIN_PATTERN_LENGTH
    ps.maxlen = MAX_PATTERN_LENGTH

    pool_size = TOP_K * OVERMINE_MULTIPLIER
    raw = ps.topk(pool_size, closed=True)
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]

    raw.sort(key=lambda t: -t[0])
    raw = raw[:TOP_K]

    return [(sup, [inv_vocab[v] for v in pat]) for sup, pat in raw]


def main() -> None:
    load_dotenv()
    sequences = build_sequences(engine)
    n_patients = len(sequences)
    print(f"[v2] {n_patients} patient sequences")

    mined = mine(sequences)
    print(f"[v2] {len(mined)} closed patterns (from pool of {TOP_K * OVERMINE_MULTIPLIER})\n")

    for rank, (sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        print(f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] {pattern_to_str(pat)}")


if __name__ == "__main__":
    main()
