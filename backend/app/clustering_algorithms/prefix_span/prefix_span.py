# python app/clustering_algorithms/prefix_span/prefix_span.py
# python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4
# python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4 --shuffle --shuffle-seed 42   # temporal null test (no DB write)

# custom optimizations (7):
# 1. over-mining: mine a candidate pool 20x larger than the final result set (closed=True,
#    TOP_K * OVERMINE_MULTIPLIER), so later filters can prune aggressively without running out of candidates
# 2. GML re-ranking: rank patterns by geometric mean lift instead of raw support
# 3. type diversity bonus + same-type-run filter: multiply GML by (1 + 0.3 * (n_types - 1)) to boost
#    patterns spanning C, M, P, CP together, and drop patterns like P->P->P that repeat the same event type
#    3 times in a row
# 4. full-spectrum quota (Phase A): reserve 25 slots for patterns spanning all 4 event types before normal fill
# 5. Jaccard dedup: skip a candidate if it shares >= 80% of items with an already-chosen pattern
# 6. prefix/suffix/dental caps: at most 6 patterns starting with the same item, 20 ending with the same
#    item, and at most 15 patterns where >= 50% of unique items are dental
# 7. cross-scope dedup: per-cluster results drop patterns already mined globally

# GML is always < 1 for sequential patterns:
# every patient who has the pattern also has each item individually -> P(pattern) <= P(any item)
# therefore: P(pattern) <= min(P(item1), P(item2), ...) <= geometric_mean(P(item1), ...)
# GML = P(pattern) / geometric_mean(...) <= 1 always
# higher GML (closer to 1) = items tend to appear together in sequence -> more interesting pattern

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
# package-qualified so this save_results module doesn't collide with the
# k_prototypes save_results module when both are imported in-process
from clustering_algorithms.prefix_span.save_results import save_prefix_span_results


MIN_SUPPORT_PCT = 0.01  # how many patients have the sequence (22.284 x 0.01)
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

OVERMINE_MULTIPLIER = 20  # used to extend the searching space to 10.000
TYPE_DIVERSITY_BONUS = 0.3  # increase GML score for patterns that have more unique item types in the sequence

JACCARD_THRESHOLD = 0.80  # shows how similar 2 patterns are
MAX_PER_PREFIX = 6
MAX_PER_SUFFIX = 20
MAX_DENTAL_PATTERNS = 15  # at most MAX_DENTAL_PATTERNS patterns where >=50% of unique items are dental

# guarantee a minimum number of full-spectrum trajectory patterns in TOP_K,
# so the M+P-heavy pool can't crowd out the rare C+M+P+CP stories
MULTITYPE_MIN_TYPES = 4          # how many distinct type-prefixes counts as "full spectrum"
MIN_MULTITYPE_PATTERNS = 25      # reserved slots (include all distinct 4-type patterns up to this many)

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

# these findings are only noise: redundant for a lot of visits
SOCIAL_STATUS_SUBSTRINGS: frozenset[str] = frozenset({
    "full-time employment",
    "part-time employment",
    "not in labor force",
    "unemployed",
    "social isolation",
    "limited social contact",
    "received higher education",
    "stress (finding)",
})

# if two events have the same date, order will be: C -> M -> P -> CP
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

# 70197 careplans
# 727499 conditions
# 913100 medications
# 3225114 procedures
# load events returns all of them -> 4.935.910 events


def build_sequences(
    engine,
    cluster_label: Optional[int] = None,
    shuffle_seed: Optional[int] = None,
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
    events = events[~blacklist_mask]  # remove all the blacklisted items
    print(f"  removed {blacklist_mask.sum():,} blacklisted events")

    # drop psychosocial/SDOH status findings (see SOCIAL_STATUS_SUBSTRINGS): they
    # sit on most wellness visits and only add a vague antecedent to the
    # screening battery, inflating near-duplicate patterns
    sdoh_lower = events["item"].str.lower()
    sdoh_mask = pd.Series(False, index=events.index)
    for sub in SOCIAL_STATUS_SUBSTRINGS:
        sdoh_mask |= sdoh_lower.str.contains(sub, regex=False)
    events = events[~sdoh_mask]
    print(f"  removed {sdoh_mask.sum():,} social-status events")

    # keep only the last WINDOW_DAYS per patient
    maxd = events.groupby("patient_id", sort=False)["event_date"].transform("max")
    cutoff = maxd - pd.Timedelta(days=WINDOW_DAYS)
    events = events[events["event_date"] >= cutoff]

    # delete duplicate consecutive items
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

    # temporal-shuffle null test: permute each patient's timeline in place. The item
    # set per patient stays the same (single-item supports, and so the GML denominator,
    # are unchanged), only order is destroyed -> any GML drop is due purely to ordering.
    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        for seq in sequences:
            rng.shuffle(seq)
        print(f"  [null test] permuted each patient's event order (seed={shuffle_seed})")

    print(f"  built {len(sequences):,} patient sequences")
    return sequences, patient_ids

# build_sequences returns a list of lists, where each list is the patient chronological history.


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

# encodes each string to an integer as the prefixSpan lib. works with
# integers, not strings. there are 1172 unique items -> 311 unique C,
# 398 unique M, 423 unique P, 40 unique CP


# verifies if short is subsequence of long
def _is_subsequence(pattern: list[str], sequence: list[str]) -> bool:
    it = iter(sequence)
    return all(any(item == p for item in it) for p in pattern)


# measures how similar 2 sets are: Jaccard(A, B) = |A and B| / |A or B|
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
    shuffle_seed: Optional[int] = None,
) -> list[tuple[int, list[str]]]:
    if not sequences:
        return []

    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * min_support_pct))  # 1% of the patients, min 2

    int_seqs, inv_vocab = _encode(sequences)
    # [C:Diabet, M:Metformin, P:Bloodtest] -> [C, M, P]
    item_type = np.array([s.split(":", 1)[0] for s in inv_vocab])

    def _n_types(pat: list[int]) -> int:
        return len({item_type[v] for v in set(pat)})

    # single_support = nr of patients that have at least once the event i
    single_support = np.zeros(len(inv_vocab), dtype=np.int32)
    for seq in int_seqs:
        single_support[list(set(seq))] += 1

    ps = PrefixSpan(int_seqs)
    ps.minlen = min_pattern_length
    ps.maxlen = max_pattern_length

    pool_size = top_k * OVERMINE_MULTIPLIER
    print(f"  running PrefixSpan (n={n_patients:,}, minsup={abs_minsup}, pool={pool_size})...")
    raw = ps.topk(pool_size, closed=True)  # drops A -> B if it finds A -> B -> C with the same support
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]
    print(f"  {len(raw)} raw patterns above support floor")

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
        if len(pat) < min_pattern_length or sup < abs_minsup:
            continue
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
    print(f"  {len(filtered)} after type-run filter")

    if not filtered:
        return []

    pool_size = min(len(filtered), top_k * OVERMINE_MULTIPLIER)
    filtered.sort(key=lambda t: (-t[1], -t[0]))
    pool_candidates = filtered[:pool_size]

    # drop pattern P if there exists a longer pattern P' with the same support
    # where P is a subsequence of P' -> P is redundant
    pool_fsets = []
    for _gml, _sup, pat in pool_candidates:
        pool_fsets.append(frozenset(pat))

    # group indices by support so we only compare patterns with equal support
    sup_to_idx = {}
    for idx in range(len(pool_candidates)):
        sup = pool_candidates[idx][1]
        if sup not in sup_to_idx:
            sup_to_idx[sup] = []
        sup_to_idx[sup].append(idx)

    # verifies if short is subsequence of long
    def _is_int_subseq(short: list[int], long: list[int]) -> bool:
        it = iter(long)
        return all(any(x == s for x in it) for s in short)

    non_dominated = set()
    for idx in range(len(pool_candidates)):
        _gml, sup, pat = pool_candidates[idx]
        pat_fset = pool_fsets[idx]
        dominated = False
        for other_idx in sup_to_idx.get(sup, []):
            other_pat = pool_candidates[other_idx][2]
            is_longer = len(other_pat) > len(pat)
            items_subset = pat_fset.issubset(pool_fsets[other_idx])
            is_subseq = _is_int_subseq(pat, other_pat)
            if is_longer and items_subset and is_subseq:
                dominated = True
                break
        if not dominated:
            non_dominated.add(idx)

    pool_candidates = [pool_candidates[i] for i in range(len(pool_candidates)) if i in non_dominated]
    print(f"  {len(pool_candidates)} after closedness filter")

    pool_candidates.sort(key=lambda t: (-t[0], -t[1], len(t[2])))
    pool = pool_candidates

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

    chosen: list[tuple[float, int, list[int]]] = []
    chosen_sets: list[tuple[frozenset, int]] = []  # [(frozenset, len)] for Jaccard comparison
    chosen_dental: list[bool] = []
    chosen_idx: set[int] = set()
    prefix_counts: dict[int, int] = {}  # how many chosen patterns start with item X
    suffix_counts: dict[int, int] = {}  # how many chosen patterns end with item X
    dental_count = [0]

    def _try_select(idx: int, entry, *, enforce_caps: bool) -> bool:
        lead = entry[2][0]   # first item
        tail = entry[2][-1]  # last item
        if enforce_caps:
            if prefix_counts.get(lead, 0) >= MAX_PER_PREFIX:
                return False
            if suffix_counts.get(tail, 0) >= MAX_PER_SUFFIX:
                return False
        is_dental = _is_dental_majority(entry[2])
        if is_dental and dental_count[0] >= MAX_DENTAL_PATTERNS:
            return False
        pat_set = frozenset(entry[2])
        pat_len = len(pat_set)
        # check Jaccard similarity with all already chosen patterns
        if not all(_jaccard(pat_set, pat_len, s, s_len) < JACCARD_THRESHOLD for s, s_len in chosen_sets):
            return False
        chosen.append(entry)
        chosen_sets.append((pat_set, pat_len))
        chosen_dental.append(is_dental)
        chosen_idx.add(idx)
        prefix_counts[lead] = prefix_counts.get(lead, 0) + 1
        suffix_counts[tail] = suffix_counts.get(tail, 0) + 1
        if is_dental:
            dental_count[0] += 1
        return True

    # Phase A - reserve a quota of full-spectrum (multi-type) trajectories. These
    # bypass the prefix/suffix caps (still Jaccard-deduped and dental-capped) so a
    # genuine C->CP->M->P story is never crowded out by the M+P-heavy pool.
    multitype_count = 0
    for idx, entry in enumerate(pool):
        if multitype_count >= MIN_MULTITYPE_PATTERNS:
            break
        if _n_types(entry[2]) < MULTITYPE_MIN_TYPES:
            continue
        if _try_select(idx, entry, enforce_caps=False):
            multitype_count += 1
    print(f"  {multitype_count} multi-type patterns reserved (>= {MULTITYPE_MIN_TYPES} types)")

    # Phase B - normal greedy fill over the rest, enforcing all caps.
    for idx, entry in enumerate(pool):
        if len(chosen) >= top_k:
            break
        if idx in chosen_idx:
            continue
        _try_select(idx, entry, enforce_caps=True)
    print(f"  {len(chosen)} after dedup (dental kept: {dental_count[0]}/{MAX_DENTAL_PATTERNS})")

    # The quota guarantees inclusion, not ordering: re-sort by GML so rank still
    # reflects score (the file header advertises "ranked by geometric mean lift").
    order = sorted(
        range(len(chosen)),
        key=lambda i: (-chosen[i][0], -chosen[i][1], len(chosen[i][2])),
    )
    chosen = [chosen[i] for i in order]
    chosen_dental = [chosen_dental[i] for i in order]

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
        n_types = len({it.split(":", 1)[0] for it in pat})
        multitype_tag = " [4-type]" if n_types >= MULTITYPE_MIN_TYPES else ""
        line = f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%, gml={gml:.2f}]{dental_tag}{multitype_tag} {pattern_to_str(pat)}"
        print(line)
        lines.append(line)
    print("--- end of pattern list ---\n")

    scope = "global" if cluster_label is None else f"cluster_{cluster_label}"
    shuffle_tag = "" if shuffle_seed is None else f"_shuffled_seed{shuffle_seed}"
    out_path = f"patterns_{scope}{shuffle_tag}.txt"
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


# returns all pattern strings already stored for the global scope (cluster_label IS NULL)
def _existing_global_pattern_strs(db_session) -> set[str]:
    result = db_session.execute(
        text("SELECT pattern_str FROM prefix_span_pattern WHERE cluster_label IS NULL")
    )
    out: set[str] = set()
    for row in result:
        out.add(row[0])
    return out


def _drop_global_duplicates(
    mined: list[tuple[int, list[str]]],
    global_strs: set[str],
) -> list[tuple[int, list[str]]]:
    kept: list[tuple[int, list[str]]] = []
    for sup, pat in mined:
        if pattern_to_str(pat) in global_strs:
            continue
        kept.append((sup, pat))
    return kept


def _run_single(engine, db_session, cluster_label: Optional[int], shuffle_seed: Optional[int] = None) -> None:
    label_tag = "global" if cluster_label is None else f"cluster {cluster_label}"
    print(f"\nloading sequences ({label_tag})...")
    sequences, patient_ids = build_sequences(engine, cluster_label=cluster_label, shuffle_seed=shuffle_seed)
    n_patients = len(sequences)
    print(f"  {n_patients} patients with events")
    if n_patients == 0:
        print("  nothing to mine, skipping")
        return

    avg_len = sum(len(s) for s in sequences) / n_patients
    print(f"  avg sequence length: {avg_len:.1f}")

    print(f"mining patterns (minsup={MIN_SUPPORT_PCT:.0%}, top_k={TOP_K})...")
    mined = mine_patterns(sequences, cluster_label=cluster_label, shuffle_seed=shuffle_seed)
    print(f"  {len(mined)} patterns kept")

    # null test is read-only: it saves the shuffled top-K to a file but must not
    # touch dedup, memberships or the DB, or it would overwrite the real results
    if shuffle_seed is not None:
        print("  [null test] shuffle run: skipping global-dedup, membership attribution and DB write")
        return

    # Per-cluster runs only keep patterns that are distinctive to the cluster:
    # anything already mined globally is dropped so the two scopes never repeat
    # the same sequence (run the global scope first for this to take effect).
    if cluster_label is not None:
        global_strs = _existing_global_pattern_strs(db_session)
        before = len(mined)
        mined = _drop_global_duplicates(mined, global_strs)
        print(f"  dropped {before - len(mined)} patterns already present globally")

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


def run(engine, db_session, n_clusters: Optional[int] = None, shuffle_seed: Optional[int] = None) -> None:
    if n_clusters is None:
        _run_single(engine, db_session, cluster_label=None, shuffle_seed=shuffle_seed)
    else:
        labels = list(range(n_clusters)) + [-1]
        print(f"per-cluster mining: {labels}")
        for label in labels:
            print(f"\n{'='*60}  cluster {label}  {'='*60}")
            _run_single(engine, db_session, cluster_label=label, shuffle_seed=shuffle_seed)


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
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="temporal-shuffle null test: permute each patient's event order, re-mine, and "
             "write the shuffled top-K to patterns_*_shuffled_seed*.txt WITHOUT touching the "
             "database, so the GML collapse vs. the real run can be compared",
    )
    parser.add_argument(
        "--shuffle-seed",
        type=int,
        default=42,
        dest="shuffle_seed",
        help="RNG seed for --shuffle; re-run with several seeds to average the null (default 42)",
    )
    args = parser.parse_args()
    load_dotenv()
    shuffle_seed = args.shuffle_seed if args.shuffle else None
    with SessionLocal() as db:
        run(engine, db, n_clusters=args.n_clusters, shuffle_seed=shuffle_seed)
