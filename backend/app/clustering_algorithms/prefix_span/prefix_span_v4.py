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
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - v4
# - run-of-3-same-type filter: drop patterns with 3 consecutive same-type items
# - explicit closedness pass: drop pattern P if P is a subseq of P' with sup(P)=sup(P')
# - Jaccard dedup: skip a candidate if Jaccard >= 0.80 with any already-chosen
# - per-prefix cap: at most MAX_PER_PREFIX patterns starting with the same item
# - per-suffix cap: at most MAX_PER_SUFFIX patterns ending with the same item
# - dental cap: at most MAX_DENTAL_PATTERNS patterns where >=50% of unique items are dental

# python app/clustering_algorithms/prefix_span/prefix_span_v4.py

# GML is always < 1 for sequential patterns:
# every patient who has the pattern also has each item individually -> P(pattern) <= P(any item)
# therefore: P(pattern) <= min(P(item1), P(item2), ...) <= geometric_mean(P(item1), ...)
# GML = P(pattern) / geometric_mean(...) <= 1 always
# higher GML (closer to 1) = items tend to appear together in sequence -> more interesting pattern

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
TYPE_DIVERSITY_BONUS = 0.3  # increase GML score for patterns that have more unique item types in the sequence

JACCARD_THRESHOLD = 0.80          # shows how similar 2 patterns are
MAX_PER_PREFIX = 6
MAX_PER_SUFFIX = 20
MAX_DENTAL_PATTERNS = 15          # at most MAX_DENTAL_PATTERNS patterns where >=50% of unique items are dental

# events that appear for almost all patients
ITEM_BLACKLIST_SUBSTRINGS: frozenset[str] = frozenset({
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
})

# limit the frequency of dental patterns (they dominate the dataset)
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


# measures how similar 2 sets are: Jaccard(A, B) = |A ∩ B| / |A ∪ B|
def _jaccard(a: frozenset, a_len: int, b: frozenset, b_len: int) -> float:
    inter = len(a & b)
    denom = a_len + b_len - inter
    return inter / denom if denom else 0.0


# verifies if short is subsequence of long
def _is_int_subseq(short: list[int], long: list[int]) -> bool:
    it = iter(long)
    return all(any(x == s for x in it) for s in short)


def mine(sequences: list[list[str]]) -> list[tuple[int, list[str]]]:
    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))  # 1% of the patients, min 2

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

    # drops sequences with 3 items of the same type (P -> P -> P is not allowed anymore)
    def has_run_of_3_same_type(pat: list[int]) -> bool:
        if len(pat) < 3:
            return False
        types = item_type[pat]
        return bool(np.any((types[:-2] == types[1:-1]) & (types[1:-1] == types[2:])))

    # reference frequency level
    log_n = np.log(n_patients)
    # filtered collects [(gml, support, pattern)]
    filtered: list[tuple[float, int, list[int]]] = []

    # GML measures if the pattern appears more often than expected given the individual item frequencies
    for sup, pat in raw:
        if has_run_of_3_same_type(pat):
            continue
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
        n_types = len({item_type[v] for v in unique_items})  # how many different events
        gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))

        filtered.append((gml, sup, pat))

    if not filtered:
        return []

    filtered.sort(key=lambda t: (-t[1], -t[0]))

    # drop pattern P if there exists a longer pattern P' with the same support
    # where P is a subsequence of P' -> P is redundant
    pool_fsets = []
    for _gml, _sup, pat in filtered:
        pool_fsets.append(frozenset(pat))

    # group indices by support so we only compare patterns with equal support
    sup_to_idx = {}
    for idx in range(len(filtered)):
        sup = filtered[idx][1]
        if sup not in sup_to_idx:
            sup_to_idx[sup] = []
        sup_to_idx[sup].append(idx)

    non_dominated = set()
    for idx in range(len(filtered)):
        _gml, sup, pat = filtered[idx]
        pat_fset = pool_fsets[idx]
        dominated = False
        for other_idx in sup_to_idx.get(sup, []):
            other_pat = filtered[other_idx][2]
            is_longer = len(other_pat) > len(pat)
            items_subset = pat_fset.issubset(pool_fsets[other_idx])
            is_subseq = _is_int_subseq(pat, other_pat)
            if is_longer and items_subset and is_subseq:
                dominated = True
                break
        if not dominated:
            non_dominated.add(idx)

    filtered = [filtered[i] for i in range(len(filtered)) if i in non_dominated]
    filtered.sort(key=lambda t: (-t[0], -t[1], len(t[2])))

    # allow max DENTAL_KEYWORDS per run
    is_dental_item = []
    for s in inv_vocab:
        s_lower = s.lower()
        is_dental = any(kw in s_lower for kw in DENTAL_KEYWORDS)
        is_dental_item.append(is_dental)
    is_dental_item = np.array(is_dental_item)

    def _is_dental_majority(pat: list[int]) -> bool:
        uniq = set(pat)
        if not uniq:
            return False
        dental_hits = 0
        for v in uniq:
            if is_dental_item[v]:
                dental_hits += 1
        return dental_hits * 2 >= len(uniq)  # more than 50% dental

    chosen = []
    chosen_sets = []    # [(frozenset, len)] for Jaccard comparison
    prefix_counts = {}  # how many chosen patterns start with item X
    suffix_counts = {}  # how many chosen patterns end with item X
    dental_count = 0

    for entry in filtered:
        gml, sup, pat = entry
        lead = pat[0]   # first item
        tail = pat[-1]  # last item

        if prefix_counts.get(lead, 0) >= MAX_PER_PREFIX:
            continue
        if suffix_counts.get(tail, 0) >= MAX_PER_SUFFIX:
            continue

        is_dental = _is_dental_majority(pat)
        if is_dental and dental_count >= MAX_DENTAL_PATTERNS:
            continue

        pat_set = frozenset(pat)
        pat_len = len(pat_set)

        # check Jaccard similarity with all already chosen patterns
        too_similar = False
        for chosen_set, chosen_len in chosen_sets:
            if _jaccard(pat_set, pat_len, chosen_set, chosen_len) >= JACCARD_THRESHOLD:
                too_similar = True
                break

        if not too_similar:
            chosen.append(entry)
            chosen_sets.append((pat_set, pat_len))
            prefix_counts[lead] = prefix_counts.get(lead, 0) + 1
            suffix_counts[tail] = suffix_counts.get(tail, 0) + 1
            if is_dental:
                dental_count += 1

        if len(chosen) == TOP_K:
            break

    return [(gml, sup, [inv_vocab[v] for v in pat]) for gml, sup, pat in chosen]


def main() -> None:
    load_dotenv()
    sequences = build_sequences(engine)
    n_patients = len(sequences)
    print(f"[v4] {n_patients} patient sequences")

    mined = mine(sequences)
    print(f"[v4] {len(mined)} patterns (filtered + diversified)\n")

    lines: list[str] = [f"Top {len(mined)} patterns (filtered + diversified)\n"]
    for rank, (gml, sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        line = f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] [gml: {gml:.4f}] {pattern_to_str(pat)}"
        print(line)
        lines.append(line)

    out_path = "results/per_version/v4.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nsaved to {out_path}")


if __name__ == "__main__":
    main()
