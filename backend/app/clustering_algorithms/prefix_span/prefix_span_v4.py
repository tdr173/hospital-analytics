"""
PrefixSpan v4 - v3 + filtering & diversification.

Adds on top of v3:
  - run-of-3-same-type filter: drop patterns with 3 consecutive same-type items
  - explicit closedness pass: drop pattern P if P is a subseq of P' with sup(P)=sup(P')
  - Jaccard dedup: skip a candidate if Jaccard >= 0.80 with any already-chosen
  - per-prefix cap: at most MAX_PER_PREFIX patterns starting with the same item
  - per-suffix cap: at most MAX_PER_SUFFIX patterns ending with the same item
  - dental cap: at most MAX_DENTAL_PATTERNS patterns where >=50% of unique items are dental

No downstream/orchestration yet (no attribution, no per-cluster mode, no DB write).
That's v5 (= prefix_span.py).

Run from backend/:
    python app/clustering_algorithms/prefix_span/prefix_span_v4.py
"""

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


MIN_SUPPORT_PCT = 0.01
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

OVERMINE_MULTIPLIER = 20
TYPE_DIVERSITY_BONUS = 0.3

JACCARD_THRESHOLD = 0.80          # NEW in v4
MAX_PER_PREFIX = 6                # NEW in v4
MAX_PER_SUFFIX = 20               # NEW in v4
MAX_DENTAL_PATTERNS = 15          # NEW in v4

ITEM_BLACKLIST_SUBSTRINGS: frozenset[str] = frozenset({
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
})

DENTAL_KEYWORDS: frozenset[str] = frozenset({
    "dental",
    "fluoride",
    "gingiv",
    "supragingival",
    "subgingival",
    "oral health",
    "tooth",
    "teeth",
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


def _jaccard(a: frozenset, a_len: int, b: frozenset, b_len: int) -> float:
    inter = len(a & b)
    denom = a_len + b_len - inter
    return inter / denom if denom else 0.0


def _is_int_subseq(short: list[int], long: list[int]) -> bool:
    it = iter(long)
    return all(any(x == s for x in it) for s in short)


def mine(sequences: list[list[str]]) -> list[tuple[int, list[str]]]:
    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))

    int_seqs, inv_vocab = encode(sequences)
    item_type = np.array([s.split(":", 1)[0] for s in inv_vocab])

    single_support = np.zeros(len(inv_vocab), dtype=np.int32)
    for seq in int_seqs:
        single_support[list(set(seq))] += 1

    ps = PrefixSpan(int_seqs)
    ps.minlen = MIN_PATTERN_LENGTH
    ps.maxlen = MAX_PATTERN_LENGTH

    pool_size = TOP_K * OVERMINE_MULTIPLIER
    raw = ps.topk(pool_size, closed=True)
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]

    def has_run_of_3_same_type(pat: list[int]) -> bool:
        if len(pat) < 3:
            return False
        types = item_type[pat]
        return bool(np.any((types[:-2] == types[1:-1]) & (types[1:-1] == types[2:])))

    log_n = np.log(n_patients)
    filtered: list[tuple[float, int, list[int]]] = []
    for sup, pat in raw:
        if has_run_of_3_same_type(pat):
            continue
        unique_items = np.array(list(set(pat)))
        log_item_freqs = np.log(np.maximum(single_support[unique_items], 1)) - log_n
        raw_gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))
        n_types = len({item_type[v] for v in unique_items})
        gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))
        filtered.append((gml, sup, pat))

    if not filtered:
        return []

    filtered.sort(key=lambda t: (-t[1], -t[0]))
    pool_fsets = [frozenset(pat) for _c, _s, pat in filtered]
    sup_to_idx: dict[int, list[int]] = {}
    for idx, (_c, sup, _pat) in enumerate(filtered):
        sup_to_idx.setdefault(sup, []).append(idx)

    non_dominated: set[int] = set()
    for idx, (_c, sup, pat) in enumerate(filtered):
        pat_fset = pool_fsets[idx]
        dominated = False
        for other_idx in sup_to_idx.get(sup, []):
            other_pat = filtered[other_idx][2]
            if (len(other_pat) > len(pat)
                    and pat_fset.issubset(pool_fsets[other_idx])
                    and _is_int_subseq(pat, other_pat)):
                dominated = True
                break
        if not dominated:
            non_dominated.add(idx)
    filtered = [filtered[i] for i in range(len(filtered)) if i in non_dominated]

    filtered.sort(key=lambda t: (-t[0], -t[1], len(t[2])))

    is_dental_item = np.array([
        any(kw in s.lower() for kw in DENTAL_KEYWORDS) for s in inv_vocab
    ])

    def _is_dental_majority(pat: list[int]) -> bool:
        uniq = set(pat)
        if not uniq:
            return False
        dental_hits = sum(1 for v in uniq if is_dental_item[v])
        return dental_hits * 2 >= len(uniq)

    chosen: list[tuple[float, int, list[int]]] = []
    chosen_sets: list[tuple[frozenset, int]] = []
    prefix_counts: dict[int, int] = {}
    suffix_counts: dict[int, int] = {}
    dental_count = 0
    for entry in filtered:
        lead = entry[2][0]
        tail = entry[2][-1]
        if prefix_counts.get(lead, 0) >= MAX_PER_PREFIX:
            continue
        if suffix_counts.get(tail, 0) >= MAX_PER_SUFFIX:
            continue
        is_dental = _is_dental_majority(entry[2])
        if is_dental and dental_count >= MAX_DENTAL_PATTERNS:
            continue
        pat_set = frozenset(entry[2])
        pat_len = len(pat_set)
        if all(_jaccard(pat_set, pat_len, s, s_len) < JACCARD_THRESHOLD for s, s_len in chosen_sets):
            chosen.append(entry)
            chosen_sets.append((pat_set, pat_len))
            prefix_counts[lead] = prefix_counts.get(lead, 0) + 1
            suffix_counts[tail] = suffix_counts.get(tail, 0) + 1
            if is_dental:
                dental_count += 1
        if len(chosen) == TOP_K:
            break

    return [(sup, [inv_vocab[v] for v in pat]) for _gml, sup, pat in chosen]


def main() -> None:
    load_dotenv()
    sequences = build_sequences(engine)
    n_patients = len(sequences)
    print(f"[v4] {n_patients} patient sequences")

    mined = mine(sequences)
    print(f"[v4] {len(mined)} patterns (filtered + diversified)\n")

    for rank, (sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        print(f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] {pattern_to_str(pat)}")


if __name__ == "__main__":
    main()
