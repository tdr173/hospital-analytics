# - v0
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - v1
# - caps events length at 25
# - blacklists very frequent events
# - adds 2 year time period allowed
# - drops consecutive duplicate events
# - prefix-rank tie-breaking sort (C -> M -> P -> CP on two events with the same date)
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - v2
# - overmine TOP_K * OVERMINE_MULTIPLIER patterns instead of just TOP_K
# - request closed patterns (closed=True): no superset with the same support
# - select the final TOP_K by support from the closed pool
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - v3
# - GML (Geometric Mean Lift) scoring instead of ranking by support
# - type diversity bonus for patterns spanning multiple event types (C, M, P, CP)

# python app/clustering_algorithms/prefix_span/prefix_span_v3.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # backend/app/

from typing import Iterable

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine


MIN_SUPPORT_PCT = 0.01  # how many patients have the sequence (22.284 x 0.01)
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

OVERMINE_MULTIPLIER = 20  # used to extend the searching space to 10.000
TYPE_DIVERSITY_BONUS = 0.3  # NEW in v3

# events that appear for almost all patients
ITEM_BLACKLIST_SUBSTRINGS: frozenset[str] = frozenset({
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
})

# if two events have the same date, order will be: C -> M -> P -> CP
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

# 70197 careplans
# 727499 conditions
# 913100 medications
# 3225114 procedures
# load events returns all of them -> 4.935.910 events


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
    events = events[~blacklist_mask]  # remove all the blacklisted items

    maxd = events.groupby("patient_id", sort=False)["event_date"].transform("max")
    cutoff = maxd - pd.Timedelta(days=WINDOW_DAYS)
    events = events[events["event_date"] >= cutoff]

    # delete duplicate consecutive items
    same_pid = events["patient_id"].eq(events["patient_id"].shift())
    same_item = events["item"].eq(events["item"].shift())
    events = events[~(same_pid & same_item)]

    events = events.groupby("patient_id", sort=False, group_keys=False).tail(
        MAX_EVENTS_PER_PATIENT
    )

    grouped = events.groupby("patient_id", sort=False)["item"].apply(list)
    return grouped.tolist()

# build_sequences returns a list of lists, where each list is the patient chronological history.


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

# encodes each string to an integer as the prefixSpan lib. works with
# integers, not strings. there are 1172 unique items -> 311 unique C,
# 398 unique M, 423 unique P, 40 unique CP


def pattern_to_str(pattern: Iterable[str]) -> str:
    return " -> ".join(pattern)


def mine(sequences: list[list[str]]) -> list[tuple[int, list[str]]]:
    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT)) # 1% of the patients, min 2

    int_seqs, inv_vocab = encode(sequences)
    # [C:Diabet, M:Metformin, P:Bloodtest] -> [C, M, P]
    item_type = np.array([s.split(":", 1)[0] for s in inv_vocab])

    # single_support = nr of patients that have at least once the event i
    single_support = np.zeros(len(inv_vocab), dtype=np.int32)
    for seq in int_seqs:
        single_support[list(set(seq))] += 1

    ps = PrefixSpan(int_seqs)
    ps.minlen = MIN_PATTERN_LENGTH
    ps.maxlen = MAX_PATTERN_LENGTH

    pool_size = TOP_K * OVERMINE_MULTIPLIER
    raw = ps.topk(pool_size, closed=True)  # drops A -> B if it finds A -> B -> C with the same support
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]

    # v0 and v1 were stopping after first 500 patterns found. there was no guarantee that they were the best
    # these new features fix this by expanding the searching space to 10.000, then keeping the best 500

    # reference frequency level
    log_n = np.log(n_patients)
    # scored collects [(gml, support, pattern)]
    scored: list[tuple[float, int, list[int]]] = []

    # GML measures if the pattern appears more often than expected given the individual item frequencies
    for sup, pat in raw:
        unique_items = np.array(list(set(pat)))  # remove duplicates from pattern

        # log(P(item)) = log(single_support[item] / n_patients) = log(single_support[item]) - log(n_patients)
        # array with the probability of each unique element of the pattern
        # probability that a random patient has that item
        log_item_freqs = np.log(np.maximum(single_support[unique_items], 1)) - log_n

        # raw_gml = P(pattern) / geometric_mean(P(item1), ..., P(itemN))
        # P(pattern) = log(sup/n) = log(sup) - log(n)
        # log(raw_gml) = log(P/gm) = log(sup/n/gm) = log(sup) - log(n) - mean(log_item_freqs)
        raw_gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))

        # gml = raw_gml * (1.0 + 0.3 * (n_types - 1)) - bonus for patterns spanning multiple event types
        n_types = len({item_type[v] for v in unique_items}) # how many different events
        gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))

        scored.append((gml, sup, pat))

    scored.sort(key=lambda t: (-t[0], -t[1]))
    chosen = scored[:TOP_K]

    return [(gml, sup, [inv_vocab[v] for v in pat]) for gml, sup, pat in chosen]


def main() -> None:
    load_dotenv()
    sequences = build_sequences(engine)
    n_patients = len(sequences)
    print(f"[v3] {n_patients} patient sequences")

    mined = mine(sequences)
    print(f"[v3] {len(mined)} patterns (ranked by GML)\n")

    lines: list[str] = [f"Top {len(mined)} patterns (ranked by GML)\n"]
    for rank, (gml, sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        line = f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] [gml: {gml:.4f}] {pattern_to_str(pat)}"
        print(line)
        lines.append(line)

    out_path = "results/per_version/v3.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nsaved to {out_path}")


if __name__ == "__main__":
    main()
