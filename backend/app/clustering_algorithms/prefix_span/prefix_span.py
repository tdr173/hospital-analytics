"""
PrefixSpan sequence mining for clinical event timelines.

Run from backend/:
    python app/clustering_algorithms/prefix_span/prefix_span.py [--n-clusters N]

Pattern format:  "C:Condition -> M:Medication -> P:Procedure"
Prefixes: C = Condition, M = Medication, P = Procedure, CP = CarePlan
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # backend/app/

from collections import defaultdict
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine, SessionLocal
from save_results import save_prefix_span_results


# --- tunables ---

MIN_SUPPORT_PCT = 0.01
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

# mine a bigger pool first, then trim after GML reranking
OVERMINE_MULTIPLIER = 20

JACCARD_THRESHOLD = 0.80
MAX_PER_PREFIX = 6
MAX_PER_SUFFIX = 20

# each extra event type (C/M/P/CP) in a pattern boosts its score a bit
TYPE_DIVERSITY_BONUS = 0.3

# noise items that show up on basically every encounter - not useful patterns
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

# cap dental patterns so the fluoride protocol doesn't flood results
MAX_DENTAL_PATTERNS = 15


# --- data loading ---

_PREFIX_ORDER = {"C": 0, "M": 1, "P": 2, "CP": 3}


def _load_events(engine) -> pd.DataFrame:
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
    print("fetching clinical events...")
    df = pd.read_sql(query, con=engine)
    if df.empty:
        return df
    df["event_date"] = pd.to_datetime(df["event_date"])
    print(f"  {len(df):,} rows across {df['patient_id'].nunique():,} patients")
    return df


# --- sequence construction ---

def build_sequences(
    engine,
    cluster_label: Optional[int] = None,
) -> tuple[list[list[str]], list[str]]:
    events = _load_events(engine)
    if events.empty:
        return [], []

    if cluster_label is not None:
        print(f"  restricting to cluster {cluster_label}...")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT patient_id FROM cluster_patient WHERE cluster_label = :label"),
                {"label": cluster_label},
            )
            cluster_pids = {str(row[0]) for row in result}
        events = events[events["patient_id"].astype(str).isin(cluster_pids)]
        print(f"  {len(cluster_pids):,} patients in cluster, {events['patient_id'].nunique():,} have events")

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
    print(f"  removed {blacklist_mask.sum():,} blacklisted events")

    # keep only the last WINDOW_DAYS per patient
    maxd = events.groupby("patient_id", sort=False)["event_date"].transform("max")
    cutoff = maxd - pd.Timedelta(days=WINDOW_DAYS)
    events = events[events["event_date"] >= cutoff]

    # drop consecutive duplicate items within the same patient
    same_pid = events["patient_id"].eq(events["patient_id"].shift())
    same_item = events["item"].eq(events["item"].shift())
    events = events[~(same_pid & same_item)]

    # cap timeline length per patient
    events = events.groupby("patient_id", sort=False, group_keys=False).tail(
        MAX_EVENTS_PER_PATIENT
    )

    grouped = events.groupby("patient_id", sort=False)["item"].apply(list)
    sequences = grouped.tolist()
    patient_ids = [str(p) for p in grouped.index.tolist()]
    print(f"  built {len(sequences):,} patient sequences")
    return sequences, patient_ids


# --- mining ---

def _encode(sequences: list[list[str]]) -> tuple[list[list[int]], list[str]]:
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


def _is_subsequence(pattern: list[str], sequence: list[str]) -> bool:
    it = iter(sequence)
    return all(any(item == p for item in it) for p in pattern)


def _jaccard(a: frozenset, a_len: int, b: frozenset, b_len: int) -> float:
    inter = len(a & b)
    denom = a_len + b_len - inter
    return inter / denom if denom else 0.0


def mine_patterns(
    sequences: list[list[str]],
    min_support_pct: float = MIN_SUPPORT_PCT,
    min_pattern_length: int = MIN_PATTERN_LENGTH,
    max_pattern_length: int = MAX_PATTERN_LENGTH,
    top_k: int = TOP_K,
    cluster_label: Optional[int] = None,
) -> list[tuple[int, list[str]]]:
    if not sequences:
        return []

    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * min_support_pct))

    int_seqs, inv_vocab = _encode(sequences)
    item_type = np.array([s.split(":", 1)[0] for s in inv_vocab])

    single_support = np.zeros(len(inv_vocab), dtype=np.int32)
    for seq in int_seqs:
        single_support[list(set(seq))] += 1

    ps = PrefixSpan(int_seqs)
    ps.minlen = min_pattern_length
    ps.maxlen = max_pattern_length

    pool_size = top_k * OVERMINE_MULTIPLIER
    print(f"  running PrefixSpan (n={n_patients:,}, minsup={abs_minsup}, pool={pool_size})...")
    raw = ps.topk(pool_size, closed=True)
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]
    print(f"  {len(raw)} raw patterns above support floor")

    def has_run_of_3_same_type(pat: list[int]) -> bool:
        if len(pat) < 3:
            return False
        types = item_type[pat]
        return bool(np.any((types[:-2] == types[1:-1]) & (types[1:-1] == types[2:])))

    log_n = np.log(n_patients)

    filtered: list[tuple[float, int, list[int]]] = []
    for sup, pat in raw:
        if len(pat) < min_pattern_length or sup < abs_minsup:
            continue
        if has_run_of_3_same_type(pat):
            continue
        unique_items = np.array(list(set(pat)))
        log_item_freqs = np.log(np.maximum(single_support[unique_items], 1)) - log_n
        raw_gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))
        n_types = len({item_type[v] for v in unique_items})
        gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))
        filtered.append((gml, sup, pat))
    print(f"  {len(filtered)} after type-run filter")

    if not filtered:
        return []

    pool_size = min(len(filtered), top_k * OVERMINE_MULTIPLIER)
    filtered.sort(key=lambda t: (-t[1], -t[0]))
    pool_candidates = filtered[:pool_size]

    pool_fsets = [frozenset(pat) for _c, _s, pat in pool_candidates]
    sup_to_idx: dict[int, list[int]] = {}
    for idx, (_c, sup, _pat) in enumerate(pool_candidates):
        sup_to_idx.setdefault(sup, []).append(idx)

    def _is_int_subseq(short: list[int], long: list[int]) -> bool:
        it = iter(long)
        return all(any(x == s for x in it) for s in short)

    non_dominated: set[int] = set()
    for idx, (_c, sup, pat) in enumerate(pool_candidates):
        pat_fset = pool_fsets[idx]
        dominated = False
        for other_idx in sup_to_idx.get(sup, []):
            other_pat = pool_candidates[other_idx][2]
            if (len(other_pat) > len(pat)
                    and pat_fset.issubset(pool_fsets[other_idx])
                    and _is_int_subseq(pat, other_pat)):
                dominated = True
                break
        if not dominated:
            non_dominated.add(idx)
    pool_candidates = [pool_candidates[i] for i in range(len(pool_candidates)) if i in non_dominated]
    print(f"  {len(pool_candidates)} after closedness filter")

    pool_candidates.sort(key=lambda t: (-t[0], -t[1], len(t[2])))
    pool = pool_candidates

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
    chosen_dental: list[bool] = []
    prefix_counts: dict[int, int] = {}
    suffix_counts: dict[int, int] = {}
    dental_count = 0
    for entry in pool:
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
            chosen_dental.append(is_dental)
            prefix_counts[lead] = prefix_counts.get(lead, 0) + 1
            suffix_counts[tail] = suffix_counts.get(tail, 0) + 1
            if is_dental:
                dental_count += 1
        if len(chosen) == top_k:
            break
    print(f"  {len(chosen)} after dedup (dental kept: {dental_count}/{MAX_DENTAL_PATTERNS})")

    mined: list[tuple[int, list[str]]] = [
        (sup, [inv_vocab[v] for v in pat]) for _conf, sup, pat in chosen
    ]

    str_to_idx = {s: i for i, s in enumerate(inv_vocab)}
    lines: list[str] = [f"Top {len(mined)} patterns (ranked by geometric mean lift)\n"]
    print(f"\n--- top {len(mined)} patterns ---")
    for rank, ((sup, pat), is_dental) in enumerate(zip(mined, chosen_dental), start=1):
        pct = 100.0 * sup / n_patients
        unique_idx = np.array(list({str_to_idx[it] for it in pat}))
        log_item_freqs = np.log(np.maximum(single_support[unique_idx], 1)) - log_n
        gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))
        dental_tag = " [dental]" if is_dental else ""
        line = f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%, gml={gml:.2f}]{dental_tag} {pattern_to_str(pat)}"
        print(line)
        lines.append(line)
    print("--- end of pattern list ---\n")

    out_path = "patterns_global.txt" if cluster_label is None else f"patterns_cluster_{cluster_label}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  saved to {out_path}")

    return mined


def attribute_patients(
    mined: list[tuple[int, list[str]]],
    sequences: list[list[str]],
    patient_ids: list[str],
) -> dict[int, list[str]]:
    posting: dict[str, list[int]] = defaultdict(list)
    for i, seq in enumerate(sequences):
        for it in set(seq):
            posting[it].append(i)

    memberships: dict[int, list[str]] = {}
    total = len(mined)
    for rank, (_support, pattern) in enumerate(mined, start=1):
        items_by_rarity = sorted(set(pattern), key=lambda it: len(posting.get(it, [])))
        if not items_by_rarity or not posting.get(items_by_rarity[0]):
            memberships[rank] = []
            continue
        candidates = set(posting[items_by_rarity[0]])
        for it in items_by_rarity[1:]:
            candidates &= set(posting.get(it, []))
            if not candidates:
                break

        contained = [
            patient_ids[i]
            for i in sorted(candidates)
            if _is_subsequence(pattern, sequences[i])
        ]
        memberships[rank] = contained
        if rank % 20 == 0 or rank == total:
            print(f"  attributed {rank}/{total} patterns (last: {len(contained)} matched)")
    return memberships


def pattern_to_str(pattern: Iterable[str]) -> str:
    return " -> ".join(pattern)


# --- orchestrator ---

def _run_single(engine, db_session, cluster_label: Optional[int]) -> None:
    label_tag = "global" if cluster_label is None else f"cluster {cluster_label}"
    print(f"\nloading sequences ({label_tag})...")
    sequences, patient_ids = build_sequences(engine, cluster_label=cluster_label)
    n_patients = len(sequences)
    print(f"  {n_patients} patients with events")
    if n_patients == 0:
        print("  nothing to mine, skipping")
        return

    avg_len = sum(len(s) for s in sequences) / n_patients
    print(f"  avg sequence length: {avg_len:.1f}")

    print(f"mining patterns (minsup={MIN_SUPPORT_PCT:.0%}, top_k={TOP_K})...")
    mined = mine_patterns(sequences, cluster_label=cluster_label)
    print(f"  {len(mined)} patterns kept")
    if not mined:
        print("  no patterns met thresholds, skipping write")
        return

    print("resolving patient memberships...")
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

    print("writing to db...")
    save_prefix_span_results(db_session, rows, memberships, cluster_label=cluster_label)


def run(engine, db_session, n_clusters: Optional[int] = None) -> None:
    if n_clusters is None:
        _run_single(engine, db_session, cluster_label=None)
    else:
        labels = list(range(n_clusters)) + [-1]
        print(f"per-cluster mining: {labels}")
        for label in labels:
            print(f"\n{'='*60}  cluster {label}  {'='*60}")
            _run_single(engine, db_session, cluster_label=label)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mine frequent clinical-event sequences with PrefixSpan.")
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=None,
        dest="n_clusters",
        help="mine per-cluster (0..N-1 plus -1 for outliers); reads cluster_patient table",
    )
    args = parser.parse_args()
    load_dotenv()
    with SessionLocal() as db:
        run(engine, db, n_clusters=args.n_clusters)
