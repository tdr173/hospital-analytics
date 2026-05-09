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
every event as its own step.

Algorithmic notes:
  * Events are pulled in a single UNION ALL query and prefixed in SQL.
  * Sequence construction is fully vectorised in pandas (no per-patient Python loop).
  * Items are integer-encoded before mining — PrefixSpan compares ints, not strings.
  * Mining uses `closed=True` so subpatterns of equal support are dropped automatically.
  * Patterns are re-ranked by **all-confidence** (sup / max single-item support) so the
    top-K surfaces *characteristic* sequences instead of being dominated by ubiquitous
    items. Support is the tiebreaker.
  * Patient attribution uses an inverted index: only sequences containing every pattern
    item are checked for subsequence order, instead of scanning all sequences.
"""

from collections import defaultdict
from typing import Iterable

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine, SessionLocal, clinical_read_engine
from save_results import save_prefix_span_results


# ------------------------ tunables ---------------------------------------------------

MIN_SUPPORT_PCT = 0.01
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 5
MAX_EVENTS_PER_PATIENT = 25
TOP_K = 500
WINDOW_DAYS = 730

# Over-mine factor: use topk(TOP_K * OVERMINE_MULTIPLIER) so diverse patterns
# can rise above the support-dominant ones after GML reranking.
# topk() uses a dynamic threshold — much faster than frequent(min_sup).
OVERMINE_MULTIPLIER = 20

# Jaccard similarity ceiling for the greedy dedup step.
JACCARD_THRESHOLD = 0.80

# Maximum patterns allowed to share the same first item (e.g. C:Gingivitis).
# Prevents one condition from flooding the top-K results.
MAX_PER_PREFIX = 6

# Maximum patterns allowed to share the same last item.
MAX_PER_SUFFIX = 20

# Type-diversity scoring multiplier: each additional distinct event-type prefix
# (C, M, P, CP) in a pattern multiplies its GML score by this factor.
# A 4-type pattern (C+M+P+CP) gets a 1.9x boost over a 1-type pattern,
# pushing cross-domain sequences (P->M->C) above dental-only permutations.
TYPE_DIVERSITY_BONUS = 0.3

# Items whose lowercased string contains any of these substrings are stripped
# from patient sequences before mining.  These are the truly content-free
# Synthea catch-alls attached to ~50%+ of encounters as protocol noise.
ITEM_BLACKLIST_SUBSTRINGS: frozenset[str] = frozenset({
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
})

# Items considered "dental" for quota purposes (substring match, lowercased).
# Patterns where >= 50% of items match a dental keyword count toward the
# dental quota in the dedup loop.
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

# Stop accepting new dental-majority patterns once this many are chosen.
# Lets dental sequences (gingivitis -> gingivectomy etc.) be visible without
# letting Synthea's identical fluoride protocol flood the top-K.
MAX_DENTAL_PATTERNS = 15


# ------------------------ data loading -----------------------------------------------

_PREFIX_ORDER = {"C": 0, "M": 1, "P": 2, "CP": 3}


def _load_events(engine) -> pd.DataFrame:
    """Pull every clinical event in one query, already prefixed (`C:`, `M:`, `P:`, `CP:`)."""
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
    print("  Querying all clinical events (single UNION ALL)...")
    df = pd.read_sql(query, con=engine)
    if df.empty:
        return df
    df["event_date"] = pd.to_datetime(df["event_date"])
    print(f"    {len(df):,} rows, {df['patient_id'].nunique():,} patients")
    return df


# ------------------------ sequence construction --------------------------------------

def build_sequences(engine) -> tuple[list[list[str]], list[str]]:
    """Return (sequences, patient_ids) — vectorised, no per-patient Python loop."""
    events = _load_events(engine)
    if events.empty:
        return [], []

    events["_pref"] = events["item"].str.split(":", n=1).str[0]
    events["_pref_rank"] = events["_pref"].map(_PREFIX_ORDER).fillna(99).astype(int)
    events = events.sort_values(
        ["patient_id", "event_date", "_pref_rank", "item"],
        kind="mergesort",
    )

    # Strip Synthea dental-protocol items — they appear in ~34% of patients with
    # an identical sequence and drown out all other clinical pathways.
    item_lower = events["item"].str.lower()
    blacklist_mask = pd.Series(False, index=events.index)
    for sub in ITEM_BLACKLIST_SUBSTRINGS:
        blacklist_mask |= item_lower.str.contains(sub, regex=False)
    events = events[~blacklist_mask]
    print(f"    {blacklist_mask.sum():,} dental/fluoride events removed by blacklist")

    # 2-year rolling window: keep events within WINDOW_DAYS of each patient's last event.
    maxd = events.groupby("patient_id", sort=False)["event_date"].transform("max")
    cutoff = maxd - pd.Timedelta(days=WINDOW_DAYS)
    events = events[events["event_date"] >= cutoff]

    # Collapse runs of identical items per patient. shift() compares against the previous
    # row globally; the patient_id equality guard prevents collapsing across patients.
    same_pid = events["patient_id"].eq(events["patient_id"].shift())
    same_item = events["item"].eq(events["item"].shift())
    events = events[~(same_pid & same_item)]

    # Cap per-patient timeline at the most recent N events.
    events = events.groupby("patient_id", sort=False, group_keys=False).tail(
        MAX_EVENTS_PER_PATIENT
    )

    grouped = events.groupby("patient_id", sort=False)["item"].apply(list)
    sequences = grouped.tolist()
    patient_ids = [str(p) for p in grouped.index.tolist()]
    print(f"  Built {len(sequences):,} sequences (vectorised)")
    return sequences, patient_ids


# ------------------------ mining + patient attribution -------------------------------

def _encode(sequences: list[list[str]]) -> tuple[list[list[int]], list[str]]:
    """Integer-encode item strings — much faster comparisons inside PrefixSpan."""
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
    """Two-pointer check: is `pattern` a (non-contiguous) subsequence of `sequence`?"""
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
) -> list[tuple[int, list[str]]]:
    """Run PrefixSpan and return [(support_count, pattern_items), ...] sorted by rank."""
    if not sequences:
        return []

    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * min_support_pct))

    int_seqs, inv_vocab = _encode(sequences)
    item_type = np.array([s.split(":", 1)[0] for s in inv_vocab])

    # Single-item support (number of sequences containing each item) for all-confidence.
    single_support = np.zeros(len(inv_vocab), dtype=np.int32)
    for seq in int_seqs:
        single_support[list(set(seq))] += 1

    ps = PrefixSpan(int_seqs)
    ps.minlen = min_pattern_length
    ps.maxlen = max_pattern_length

    pool_size = top_k * OVERMINE_MULTIPLIER
    print(
        f"  Running PrefixSpan topk={pool_size} (n={n_patients:,}, abs_minsup={abs_minsup}, "
        f"minlen={min_pattern_length}, maxlen={max_pattern_length})..."
    )
    # closed=True asks the library to only admit closed sequences into the
    # top-N. Without it, a single 5-step protocol can fragment into 31
    # same-support permutations and saturate the pool, pushing rarer but
    # diverse clinical pathways below the cutoff before our post-mine
    # closedness filter ever sees them.
    raw = ps.topk(pool_size, closed=True)
    # Drop patterns below the absolute minimum support floor.
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]
    print(f"  PrefixSpan returned {len(raw)} patterns (after min-support floor)")

    def has_run_of_3_same_type(pat: list[int]) -> bool:
        """True if any 3 consecutive items share the same event-type prefix."""
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
        # Geometric mean lift: how much more does this pattern occur than expected
        # if its items were independent? Uses log-space to avoid overflow.
        # gml = (sup/n) / geometric_mean(single_support[vi]/n)
        #      = exp( log(sup) - log(n) - mean(log(single_support[vi]) - log(n)) )
        unique_items = np.array(list(set(pat)))
        log_item_freqs = np.log(np.maximum(single_support[unique_items], 1)) - log_n
        raw_gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))
        n_types = len({item_type[v] for v in unique_items})
        gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))
        filtered.append((gml, sup, pat))
    print(f"  {len(filtered)} patterns after max-2-consecutive-type filter")

    if not filtered:
        return []

    # Post-mine closedness filter: drop pattern P if a strictly longer pattern Q
    # exists with the same support AND P is a subsequence of Q.  Applied to the
    # top (pool_size) patterns by support; frozenset.issubset() guards the
    # expensive subsequence scan so most pairs are rejected in O(k) time.
    pool_size = min(len(filtered), top_k * OVERMINE_MULTIPLIER)
    filtered.sort(key=lambda t: (-t[1], -t[0]))
    pool_candidates = filtered[:pool_size]

    # Precompute frozensets once; reuse in both the index and dominance check.
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
    print(f"  {len(pool_candidates)} patterns after closedness filter")

    pool_candidates.sort(key=lambda t: (-t[0], -t[1], len(t[2])))  # gml DESC, support DESC
    pool = pool_candidates

    # Pre-compute the dental flag for every vocab item once: True iff the
    # lowercased item string contains any DENTAL_KEYWORDS substring.
    is_dental_item = np.array([
        any(kw in s.lower() for kw in DENTAL_KEYWORDS) for s in inv_vocab
    ])

    def _is_dental_majority(pat: list[int]) -> bool:
        """True iff at least half of the unique items in the pattern are dental."""
        uniq = set(pat)
        if not uniq:
            return False
        dental_hits = sum(1 for v in uniq if is_dental_item[v])
        return dental_hits * 2 >= len(uniq)

    # Stage 3: greedy Jaccard dedup with prefix + suffix + dental diversity caps.
    # A candidate is accepted only if:
    #   (a) item-set Jaccard vs every already-chosen pattern < JACCARD_THRESHOLD
    #   (b) fewer than MAX_PER_PREFIX patterns share the same first item
    #   (c) fewer than MAX_PER_SUFFIX patterns share the same last item
    #   (d) if dental-majority, fewer than MAX_DENTAL_PATTERNS already chosen
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
    print(
        f"  {len(chosen)} patterns after Jaccard dedup "
        f"(threshold={JACCARD_THRESHOLD}, max_per_prefix={MAX_PER_PREFIX}, "
        f"max_per_suffix={MAX_PER_SUFFIX}, dental={dental_count}/{MAX_DENTAL_PATTERNS})"
    )

    mined: list[tuple[int, list[str]]] = [
        (sup, [inv_vocab[v] for v in pat]) for _conf, sup, pat in chosen
    ]

    str_to_idx = {s: i for i, s in enumerate(inv_vocab)}
    lines: list[str] = [f"Top {len(mined)} patterns (ranked by geometric mean lift)\n"]
    print(f"\n--- Top {len(mined)} patterns (ranked by geometric mean lift) ---")
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

    out_path = "patterns.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Patterns saved to {out_path}")

    return mined


def attribute_patients(
    mined: list[tuple[int, list[str]]],
    sequences: list[list[str]],
    patient_ids: list[str],
) -> dict[int, list[str]]:
    """For each mined pattern (rank = 1..N), list patients whose sequence contains it.

    Uses an inverted index: only sequences that contain *every* item in the pattern are
    checked for subsequence order, dropping the work from O(N) to ~O(support_count) per
    pattern.
    """
    posting: dict[str, list[int]] = defaultdict(list)
    for i, seq in enumerate(sequences):
        for it in set(seq):
            posting[it].append(i)

    memberships: dict[int, list[str]] = {}
    total = len(mined)
    for rank, (_support, pattern) in enumerate(mined, start=1):
        # Intersect posting lists, starting with the rarest item to shrink fast.
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
            print(f"  Attributed {rank}/{total} patterns (last: {len(contained)} matched)")
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
        run(clinical_read_engine, db)
