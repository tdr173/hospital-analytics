# How PrefixSpan Works — Full Walkthrough

This document explains the sequential pattern mining algorithm used in this project: what the problem is, how older algorithms approached it, how PrefixSpan improves on them, what every parameter and improvement in our implementation does, and finally two full traces — one of the bare algorithm, one of the full pipeline.

---

## 1. The Problem: Sequential Pattern Mining

A patient's clinical record is a **sequence of events ordered in time**: first they get a diagnosis, then a prescription, then a procedure, maybe another prescription. Finding **subsequences that appear in many patients' timelines** reveals common care pathways, typical disease progressions, and treatment protocols.

Formally: given a dataset of sequences D = {S₁, S₂, ..., Sₙ}, find all subsequences (patterns) that appear in at least `min_support` sequences.

**Subsequence** means order-preserving but not necessarily contiguous. Pattern [A, B] appears in [A, C, B] because A comes before B (C in between is fine).

In our case:
- Each sequence = one patient's clinical event timeline, sorted by date
- Each item = one clinical event prefixed by type (`C:` condition, `M:` medication, `P:` procedure, `CP:` care plan)
- Goal = find which event sequences recur across many patients in the same cluster (or globally)

---

## 2. Older Algorithms — The Variants

### 2.1 Apriori-based: AIS and AprioriAll (Agrawal & Srikant, 1995)

Both are breadth-first candidate-generate-then-count algorithms. They rely on the **Apriori principle**: if a pattern has support < min_support, no extension of it can have support ≥ min_support either (monotonicity). So once a pattern is infrequent, you prune the whole subtree.

**AprioriAll** works in passes over the database:
1. Count all 1-item sequences, keep those ≥ min_support.
2. Generate all 2-item candidate sequences from pairs of frequent 1-items.
3. Scan the full database to count each candidate's support.
4. Keep those ≥ min_support, generate 3-item candidates from pairs of frequent 2-item sequences.
5. Repeat until no new patterns are found.

**Problem**: Candidate explosion. If you have 500 distinct clinical events and want patterns up to length 6, the candidate count at each level grows as O(V²), O(V³), ... Each level also requires a full database scan.

For medical data with 2000+ distinct events, AprioriAll is impractical.

---

### 2.2 GSP — Generalized Sequential Patterns (Srikant & Agrawal, 1996)

GSP is an improved Apriori-style algorithm that adds:
- **Time constraints**: minimum and maximum gap between events (e.g., the second event must occur within 30 days of the first)
- **Sliding window**: events within a time window are treated as simultaneous (useful for itemset-style events)

Same multi-pass structure as AprioriAll, just with more pruning options.

**Still problematic for us**: still candidate-generate-then-count, still multiple full database scans. Time constraints are handled by us during preprocessing (the `WINDOW_DAYS` rolling window) rather than inside the algorithm, so we don't need GSP's complexity.

---

### 2.3 SPADE — Sequential Pattern Discovery using Equivalence Classes (Zaki, 2001)

SPADE uses a **vertical data format** instead of the horizontal sequences.

Instead of storing `S1: [A, B, C]`, it stores each item as an **id-list**: `A → {(S1, pos1), (S2, pos5), ...}`, meaning "item A appears at position pos1 in sequence S1, at pos5 in S2, etc."

Finding the support of pattern [A, B] = intersect A's id-list and B's id-list, keeping pairs where pos(B) > pos(A). This avoids re-scanning the database.

**Advantage**: no database rescans after the initial vertical index is built.

**Disadvantage**: id-lists can be very large. For a long sequence of N events, an item's id-list has up to N entries. Intersecting large id-lists for long patterns is expensive in memory. For our patient sequences of up to 25 events, SPADE's id-lists are manageable, but the vocabulary size (~2000+ events) makes the initial index huge.

---

### 2.4 PrefixSpan — Prefix-Projected Sequential Pattern Mining (Pei et al., 2001)

PrefixSpan doesn't generate candidates at all. It **extends prefixes depth-first** using projected databases.

**Key insight**: instead of trying all combinations, for each known frequent prefix P, build a smaller database containing only the suffixes of sequences that contain P. Mine that smaller database recursively.

Why this is better:
- **No candidates**: you only extend patterns you've already confirmed are frequent
- **Shrinking projections**: each projected database is ≤ the size of its parent, so deep recursions are cheap
- **Depth-first**: completes patterns fully before moving to the next prefix — cache-friendly, low memory footprint at any moment
- **In-practice speed**: 10–100x faster than GSP on dense data, better memory than SPADE on long sequences

The library we use (`prefixspan` Python package) implements this with an integer-encoded in-memory approach, which is the standard efficient variant.

---

## 3. PrefixSpan Core Algorithm

```
PrefixSpan(prefix P, projected_database D, min_sup):
    for each item a that is frequent in D (appears in ≥ min_sup sequences):
        P' = P + [a]          // extend the pattern
        output P' with support = count of sequences in D containing a
        D' = project(D, P')   // build suffix database for P'
        PrefixSpan(P', D', min_sup)   // recurse

project(D, P):
    for each sequence S in D that contains P as a subsequence:
        find the first occurrence of the last item of P in S
        take everything after that position as the suffix
    return those suffixes
```

Recursion bottoms out when:
- No frequent items remain in the projected database (nothing extends P)
- The pattern reaches `maxlen`

The algorithm naturally discovers every frequent sequential pattern without ever considering an infrequent one (because the projection for an infrequent prefix would be empty and excluded).

---

## 4. Our Implementation: Parameters, Steps, and Improvements

### 4.1 Parameters

```python
MIN_SUPPORT_PCT = 0.01       # a pattern must appear in ≥ 1% of patients
MIN_PATTERN_LENGTH = 3       # discard patterns with fewer than 3 events
MAX_PATTERN_LENGTH = 6       # discard patterns with more than 6 events
MAX_EVENTS_PER_PATIENT = 25  # truncate timelines to the 25 most recent events
TOP_K = 500                  # keep the final 500 patterns
WINDOW_DAYS = 730            # use only the last 2 years of each patient's history
OVERMINE_MULTIPLIER = 20     # mine TOP_K × 20 = 10,000 raw patterns before filtering
JACCARD_THRESHOLD = 0.80     # two patterns are "near-duplicates" if item overlap ≥ 80%
MAX_PER_PREFIX = 6           # at most 6 patterns may share the same first event
MAX_PER_SUFFIX = 20          # at most 20 patterns may share the same last event
TYPE_DIVERSITY_BONUS = 0.3   # each extra event type in a pattern adds 30% to its score
MAX_DENTAL_PATTERNS = 15     # cap dental-protocol patterns at 15 total
```

**Why `OVERMINE_MULTIPLIER = 20`?**

PrefixSpan ranks by raw support count: patterns that appear in more patients rank higher. But a pattern like "Medication review → HbA1c" might appear in 80% of patients simply because both events are near-universal — that's not an interesting clinical finding. We want patterns that are informative, not just common. So we mine 10,000 patterns first, rerank them by a better score (GML, explained below), then take the top 500. If we only mined 500 by raw support, we'd miss many informative but medium-support patterns.

**Why `MIN_PATTERN_LENGTH = 3`?**

2-item sequences are almost always trivially true (e.g., "diagnosed → prescribed"). Length 3 is the minimum to be a meaningful care pathway.

**Why `WINDOW_DAYS = 730`?**

Very old events (5-10 years ago) belong to a different healthcare context and can pollute the pattern. The last 2 years give a relevant, comparable window across patients.

**Why `MAX_EVENTS_PER_PATIENT = 25`?**

Patients with 200+ events dominate projections and slow down mining. Capping at 25 (most recent) keeps runtime bounded while preserving the recent trajectory.

---

### 4.2 Preprocessing Pipeline

Before PrefixSpan sees any data, `build_sequences()` runs 5 transformation steps in order:

**Step 1 — Load and label events**

`_load_events()` runs one SQL query with four UNION ALL branches, pulling from `condition`, `medication`, `procedure`, and `careplan` tables. Each event gets a type prefix: `C:`, `M:`, `P:`, `CP:`. Result: one flat DataFrame with columns `(patient_id, event_date, item)`.

**Step 2 — Sort by (patient, date, type, name)**

Within the same day, events are ordered by type: conditions first (type rank 0), then medications (1), then procedures (2), then care plans (3). Within the same type on the same day, alphabetical. This makes the ordering deterministic and meaningful: diagnoses before treatments.

**Step 3 — Blacklist noise items**

Items containing any of these substrings are dropped:
- `"assessment of health and social care needs"` — appears on nearly every encounter, meaningless as a sequence element
- `"medication review due"` — administrative marker, not a clinical event
- `"medication reconciliation"` — same

These are identified empirically as Synthea-generated noise that inflates support without clinical signal.

**Step 4 — Rolling window**

For each patient, find their most recent event date, then drop all events older than `WINDOW_DAYS` (730 days) before that date. Each patient gets up to 2 years of their most recent history.

**Step 5 — Consecutive deduplication**

Drop any event that is the same as the immediately preceding event for the same patient. This handles cases where an event is recorded multiple times on the same encounter (e.g., "Type 2 Diabetes → Type 2 Diabetes → Metformin" becomes "Type 2 Diabetes → Metformin").

**Step 6 — Cap at 25 events**

Take only the last `MAX_EVENTS_PER_PATIENT = 25` events per patient after all the above filtering. This bounds sequence length for the mining step.

---

### 4.3 Mining Step

```python
int_seqs, inv_vocab = _encode(sequences)
ps = PrefixSpan(int_seqs)
ps.minlen = 3
ps.maxlen = 6
raw = ps.topk(pool_size, closed=True)
raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]
```

**Integer encoding (`_encode`)**

The library works on integers for speed. Each unique item string gets mapped to an integer (its position in a vocabulary list). `inv_vocab[i]` maps back from integer to string. This avoids string comparisons in the inner loop.

**`ps.topk(pool_size, closed=True)`**

- `topk(n)` returns the n patterns with the highest support count. No minimum threshold — just take the top n.
- `closed=True` means **closed sequential patterns**: a pattern P is closed if no proper supersequence of P (a sequence that contains P as a subsequence and has at least one more element) has the same support as P. Closed patterns are a lossless compression of the full pattern set — from closed patterns you can reconstruct every pattern and its support. This dramatically reduces output size without losing information.

After the library returns, we still apply `abs_minsup` as a floor: `abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))`. At 1% threshold with 5000 patients, `abs_minsup = 50`. At 1% with 200 patients in a small cluster, `abs_minsup = max(2, 2) = 2` (the floor prevents min_support of 1, which returns every possible pattern).

**`pool_size = TOP_K * OVERMINE_MULTIPLIER = 10,000`**

We ask for 10,000 closed patterns from PrefixSpan. These are ranked purely by support count (most common first). Then our post-mining pipeline reranks and thins them to the final 500.

---

### 4.4 Improvement 1 — Run-of-3 Same-Type Filter

```python
def has_run_of_3_same_type(pat: list[int]) -> bool:
    types = item_type[pat]
    return bool(np.any((types[:-2] == types[1:-1]) & (types[1:-1] == types[2:])))
```

A pattern is discarded if it contains **three or more consecutive events of the same type prefix** (C/M/P/CP).

Example: `[M:Metformin, M:Insulin, M:Glipizide]` is all M-type → removed.

**Why**: such patterns are almost always protocol artifacts. Three consecutive medications without an intervening diagnosis or procedure rarely represents a meaningful clinical story — it's just "patient is on multiple medications." Procedures run as a batch (same type, same day) also produce these. Removing them biases the output toward cross-type patterns that tell a more complete story.

---

### 4.5 Improvement 2 — Geometric Mean Lift (GML) Reranking

After the run-of-3 filter, each surviving pattern gets a GML score:

```python
log_item_freqs = np.log(np.maximum(single_support[unique_items], 1)) - log_n
raw_gml = float(np.exp(np.log(sup) - log_n - np.mean(log_item_freqs)))
n_types = len({item_type[v] for v in unique_items})
gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))
```

**What GML measures**:

The lift of a pattern is its actual support divided by the support expected if all items occurred independently. GML is the geometric-mean version:

```
GML(P) = support(P) / n_patients
         ─────────────────────────────────────────────────────────
         geometric_mean( support(itemᵢ) / n_patients for i in P )
```

Geometrically: GML > 1 means the items co-occur more than chance predicts. GML = 1 means independence. GML < 1 means the items avoid each other.

**Intuition**: A pattern that appears in 80% of patients but whose items are each individually also in 80% of patients has GML ≈ 1 — the co-occurrence is just what you'd expect from common events happening to the same common patients. A pattern that appears in 40% of patients but whose items are each individually in 20% of patients has GML ≈ 2 — these events attract each other.

We mine 10,000 by support, rerank by GML, then take top 500. This surfaces informative mid-frequency patterns that pure support ranking buries under ubiquitous-but-uninformative ones.

**Type diversity bonus**:

```python
gml = raw_gml * (1.0 + TYPE_DIVERSITY_BONUS * (n_types - 1))
```

A pattern spanning 2 distinct type prefixes (e.g., C and M) gets multiplied by 1.3. Spanning 3 types gets 1.6. This nudges the ranker to prefer cross-domain patterns (diagnosis + medication + procedure) over single-domain ones (medication × 3), because cross-domain patterns are clinically more interpretable and informative.

---

### 4.6 Improvement 3 — Post-Mine Closedness Filter

```python
for idx, (_c, sup, pat) in enumerate(pool_candidates):
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
```

Even after mining with `closed=True`, the 10,000-pattern pool (restricted by GML and the type-run filter) can contain patterns where a shorter pattern's items are a subset of a longer pattern's items at the **same support**. The shorter one is redundant: everything it tells you is already told by the longer one.

A pattern P is **dominated** by Q if:
- Q is longer than P
- every item in P is also in Q (as a frozenset)
- P is a subsequence of Q (ordering preserved)
- Q has the same support as P

Dominated patterns are removed. This is a focused pass only within patterns that share the same support count (the `sup_to_idx` index), so it's efficient.

**Why this isn't fully covered by the library's `closed=True`**: The library's closed mining is computed over the full database at the database level. Our pool is a post-hoc subset (top 10,000 by support), and patterns that were non-dominated in the full database might become dominated relative to each other within this restricted pool. This filter catches those.

---

### 4.7 Improvement 4 — Greedy Jaccard Deduplication

After closedness filtering, the pool is sorted by GML descending. Patterns are added to the final set greedily:

```python
if all(_jaccard(pat_set, pat_len, s, s_len) < JACCARD_THRESHOLD for s, s_len in chosen_sets):
    chosen.append(entry)
```

A new pattern is accepted only if its Jaccard similarity to every already-accepted pattern is below 0.80.

**Jaccard similarity for sequences**:
```
Jaccard(A, B) = |items(A) ∩ items(B)| / |items(A) ∪ items(B)|
```

Note: we use **frozenset** of items (not considering order or multiplicity for the Jaccard calculation). Two patterns with 80%+ overlapping items are treated as near-duplicates, and the one ranked lower (by GML) is dropped.

**Why**: Without this, the output gets flooded by minor variations of the same pattern. "Diabetes → Metformin → HbA1c" and "Diabetes → Metformin → HbA1c → Insulin" would both make the cut by GML, but they're really the same clinical story at different lengths. We keep the better-ranked one (higher GML) and discard the rest.

---

### 4.8 Improvement 5 — Diversity Caps

Three hard caps prevent any single item from dominating the output:

```python
if prefix_counts.get(lead, 0) >= MAX_PER_PREFIX:  # lead = first item of pattern
    continue
if suffix_counts.get(tail, 0) >= MAX_PER_SUFFIX:  # tail = last item
    continue
if is_dental and dental_count >= MAX_DENTAL_PATTERNS:
    continue
```

**`MAX_PER_PREFIX = 6`**: at most 6 patterns may start with the same event. If "Diabetes" is the most common first event, you can have at most 6 patterns that begin with it, regardless of how many more would pass all other filters.

**`MAX_PER_SUFFIX = 20`**: at most 20 patterns may end with the same event. Less restrictive because endings are more varied.

**`MAX_DENTAL_PATTERNS = 15`**: Synthea generates a realistic dental-hygiene protocol (fluoride treatment, supragingival scaling, etc.) that is followed by most patients. Without this cap, dental patterns would crowd out almost all other results simply because the protocol is applied uniformly. We allow up to 15 dental patterns to represent the protocol, then stop.

A pattern is "dental majority" if more than half its unique items contain any of: `dental`, `fluoride`, `gingiv`, `supragingival`, `subgingival`, `oral health`, `tooth`, `teeth`.

---

### 4.9 Patient Attribution

After mining, we need to know which patients match each pattern. Naively, checking every pattern against every patient is O(n_patterns × n_patients × seq_len). For 500 patterns and 5000 patients, that's 2.5M subsequence checks.

Instead we use an **inverted index**:

```python
posting: dict[str, list[int]] = defaultdict(list)
for i, seq in enumerate(sequences):
    for it in set(seq):
        posting[it].append(i)
```

`posting[item]` = list of patient indices whose sequence contains `item`. For each pattern P:

1. Sort pattern items by rarity (shortest posting list = rarest item first).
2. Start with the candidate set = patients who have the rarest item.
3. For each subsequent item, intersect with its posting list. Candidates can only shrink.
4. After intersecting all items: check actual subsequence order only on the surviving candidates.

Because we start from the rarest item, the candidate set collapses quickly. In the best case (one very rare item), we check subsequence order on just a handful of patients instead of all 5000.

---

## 5. Trace 1 — Pure PrefixSpan (No Improvements)

We use a small toy dataset of 6 patients with 7 distinct clinical events. This trace shows only what the core PrefixSpan algorithm does, ignoring our preprocessing and post-mining filters.

### Dataset

```
Patient | Sequence
--------|--------------------------------------------------
P1      | [C:Diabetes, M:Metformin, P:HbA1c, M:Insulin]
P2      | [C:Diabetes, M:Metformin, P:HbA1c]
P3      | [C:Hypertension, M:Metformin, P:HbA1c, P:ECG]
P4      | [C:Diabetes, M:Metformin, M:Insulin, P:ECG]
P5      | [C:Hypertension, M:Lisinopril, P:ECG]
P6      | [C:Diabetes, M:Metformin, P:HbA1c, P:ECG]
```

### Integer encoding

```
0 → C:Diabetes       (appears in P1,P2,P4,P6)
1 → M:Metformin      (appears in P1,P2,P3,P4,P6)
2 → P:HbA1c          (appears in P1,P2,P3,P6)
3 → M:Insulin        (appears in P1,P4)
4 → C:Hypertension   (appears in P3,P5)
5 → P:ECG            (appears in P3,P4,P5,P6)
6 → M:Lisinopril     (appears in P5)
```

Encoded sequences:

```
P1: [0, 1, 2, 3]
P2: [0, 1, 2]
P3: [4, 1, 2, 5]
P4: [0, 1, 3, 5]
P5: [4, 6, 5]
P6: [0, 1, 2, 5]
```

Settings: `min_support = 2`, `min_length = 2`, `max_length = 4`.

---

### Step 1 — Count all 1-item sequences (scan the full database)

For each item, count how many sequences contain it (at least once):

```
Item 0 (C:Diabetes):     P1, P2, P4, P6    → support 4
Item 1 (M:Metformin):    P1, P2, P3, P4, P6 → support 5
Item 2 (P:HbA1c):        P1, P2, P3, P6    → support 4
Item 3 (M:Insulin):      P1, P4            → support 2
Item 4 (C:Hypertension): P3, P5            → support 2
Item 5 (P:ECG):          P3, P4, P5, P6   → support 4
Item 6 (M:Lisinopril):   P5               → support 1  ← pruned (< 2)
```

Frequent 1-items: `{0, 1, 2, 3, 4, 5}`. Item 6 is infrequent and never explored.

---

### Step 2 — For each frequent 1-item, project and recurse

PrefixSpan processes these depth-first, starting with prefix `[0]`.

---

#### Prefix `[0]` (C:Diabetes) — support 4

**Projected database**: for each sequence containing item 0, take the suffix *after* the first occurrence of 0.

```
P1: [0, 1, 2, 3]  → suffix after pos 0: [1, 2, 3]
P2: [0, 1, 2]     → suffix after pos 0: [1, 2]
P4: [0, 1, 3, 5]  → suffix after pos 0: [1, 3, 5]
P6: [0, 1, 2, 5]  → suffix after pos 0: [1, 2, 5]
P3, P5: don't contain 0 → excluded
```

**Projected DB for `[0]`**:
```
P1: [1, 2, 3]
P2: [1, 2]
P4: [1, 3, 5]
P6: [1, 2, 5]
```

Frequent items in this projection (support ≥ 2):
```
Item 1: P1,P2,P4,P6 → 4  ✓ → extend to [0,1]
Item 2: P1,P2,P6    → 3  ✓ → extend to [0,2]
Item 3: P1,P4       → 2  ✓ → extend to [0,3]
Item 5: P4,P6       → 2  ✓ → extend to [0,5]
```

Output so far: `[0]` has support 4.
Recurse on each extension...

---

##### Prefix `[0,1]` (C:Diabetes → M:Metformin) — support 4

Project `[0]`'s DB on item 1:

```
P1: [1, 2, 3] → suffix after first 1: [2, 3]
P2: [1, 2]    → suffix after first 1: [2]
P4: [1, 3, 5] → suffix after first 1: [3, 5]
P6: [1, 2, 5] → suffix after first 1: [2, 5]
```

Frequent items (support ≥ 2):
```
Item 2: P1,P2,P6 → 3 ✓ → extend to [0,1,2]
Item 3: P1,P4    → 2 ✓ → extend to [0,1,3]
Item 5: P4,P6    → 2 ✓ → extend to [0,1,5]
```

Output: `[0,1]` has support 4.
Recurse...

---

###### Prefix `[0,1,2]` (C:Diabetes → M:Metformin → P:HbA1c) — support 3

Project on item 2:
```
P1: [2, 3] → suffix after 2: [3]
P2: [2]    → suffix after 2: []   (empty)
P6: [2, 5] → suffix after 2: [5]
```

Frequent items (support ≥ 2):
```
Item 3: P1 only → 1  ✗
Item 5: P6 only → 1  ✗
```

No frequent extensions. Output `[0,1,2]` with support 3. Terminal.

---

###### Prefix `[0,1,3]` (C:Diabetes → M:Metformin → M:Insulin) — support 2

Project on item 3:
```
P1: [2, 3] → suffix after first 3 in [2,3]: []  (3 is the last item)
P4: [3, 5] → suffix after 3: [5]
```

Frequent items (support ≥ 2):
```
Item 5: P4 only → 1  ✗
```

No frequent extensions. Output `[0,1,3]` with support 2. Terminal.

---

###### Prefix `[0,1,5]` (C:Diabetes → M:Metformin → P:ECG) — support 2

Project on item 5:
```
P4: [3, 5] → suffix after 5: []
P6: [2, 5] → suffix after 5: []
```

No items remain. Output `[0,1,5]` with support 2. Terminal.

---

##### Prefix `[0,2]` (C:Diabetes → P:HbA1c) — support 3

Project `[0]`'s DB on item 2:
```
P1: [1, 2, 3] → suffix after first 2 (which is at index 1): [3]
P2: [1, 2]    → suffix after 2: []
P6: [1, 2, 5] → suffix after 2: [5]
P4: [1, 3, 5] → doesn't contain 2 → excluded
```

Frequent items (support ≥ 2): Item 3 → P1 only (1). Item 5 → P6 only (1). None.

Output `[0,2]` with support 3. Terminal.

---

##### Prefix `[0,3]` (C:Diabetes → M:Insulin) — support 2

Project `[0]`'s DB on item 3:
```
P1: [1, 2, 3] → suffix after first 3 (index 2): []
P4: [1, 3, 5] → suffix after 3: [5]
```

Frequent items: Item 5 → P4 only (1). None ≥ 2.

Output `[0,3]` with support 2. Terminal.

---

##### Prefix `[0,5]` (C:Diabetes → P:ECG) — support 2

Project `[0]`'s DB on item 5:
```
P4: [1, 3, 5] → suffix after 5: []
P6: [1, 2, 5] → suffix after 5: []
```

No items remain. Output `[0,5]` with support 2. Terminal.

---

#### Prefix `[1]` (M:Metformin) — support 5

Projected DB (suffixes after first occurrence of 1):
```
P1: [1, 2, 3]  → [2, 3]
P2: [1, 2]     → [2]
P3: [4, 1, 2, 5] → [2, 5]
P4: [1, 3, 5]  → [3, 5]
P6: [1, 2, 5]  → [2, 5]
(P5 has no item 1)
```

Frequent items:
```
Item 2: P1,P2,P3,P6 → 4 ✓ → [1,2]
Item 3: P1,P4       → 2 ✓ → [1,3]
Item 5: P3,P4,P6    → 3 ✓ → [1,5]
```

Output `[1]` support 5. Recurse on each...

---

##### Prefix `[1,2]` (M:Metformin → P:HbA1c) — support 4

Projected on item 2:
```
P1: [2, 3]  → [3]
P2: [2]     → []
P3: [2, 5]  → [5]
P6: [2, 5]  → [5]
```

Frequent items:
```
Item 3: P1 only → 1 ✗
Item 5: P3,P6   → 2 ✓ → [1,2,5]
```

Output `[1,2]` support 4.

###### Prefix `[1,2,5]` (M:Metformin → P:HbA1c → P:ECG) — support 2

Projected on item 5:
```
P3: [5] → []
P6: [5] → []
```

No extensions. Output `[1,2,5]` support 2. Terminal.

---

##### Prefix `[1,3]` (M:Metformin → M:Insulin) — support 2

Projected on item 3:
```
P1: [2, 3] → []
P4: [3, 5] → [5]
```

Frequent items: Item 5 → P4 only (1). None.

Output `[1,3]` support 2. Terminal.

---

##### Prefix `[1,5]` (M:Metformin → P:ECG) — support 3

Projected on item 5:
```
P3: [2, 5] → []
P4: [3, 5] → []
P6: [2, 5] → []
```

No extensions. Output `[1,5]` support 3. Terminal.

---

#### Prefix `[2]` (P:HbA1c) — support 4

Projected DB:
```
P1: [0, 1, 2, 3] → suffix after first 2 (index 2): [3]
P2: [0, 1, 2]    → []
P3: [4, 1, 2, 5] → [5]
P6: [0, 1, 2, 5] → [5]
```

Frequent items:
```
Item 3: P1 only → 1 ✗
Item 5: P3,P6   → 2 ✓ → [2,5]
```

Output `[2]` support 4.

##### Prefix `[2,5]` (P:HbA1c → P:ECG) — support 2

Projected on item 5: all suffixes empty. Terminal.

---

#### Prefix `[3]` (M:Insulin) — support 2

Projected DB (P1, P4):
```
P1: [0, 1, 2, 3] → suffix after 3 (index 3): []
P4: [0, 1, 3, 5] → [5]
```

Frequent items: Item 5 → P4 only (1). None.

Output `[3]` support 2. Terminal (no length-2+ extensions with support ≥ 2, so `[3]` alone doesn't qualify if `min_length = 2`).

Actually wait — `min_length = 2`, so `[3]` (length 1) isn't output. PrefixSpan generates all frequent subsequences; the length filter removes those shorter than `min_length`. In practice the library's `ps.minlen = 3` means 1-item and 2-item patterns are never output.

---

#### Prefix `[4]` (C:Hypertension) — support 2

Projected DB (P3, P5):
```
P3: [4, 1, 2, 5] → suffix after 4: [1, 2, 5]
P5: [4, 6, 5]    → suffix after 4: [6, 5]
```

Frequent items:
```
Item 1: P3 only → 1 ✗
Item 2: P3 only → 1 ✗
Item 5: P3,P5   → 2 ✓ → [4,5]
Item 6: P5 only → 1 ✗
```

Output `[4]` support 2.

##### Prefix `[4,5]` (C:Hypertension → P:ECG) — support 2

Projected on item 5: all suffixes empty. Terminal.

---

#### Prefix `[5]` (P:ECG) — support 4

Projected DB (P3, P4, P5, P6): all suffixes after 5 are empty. No frequent extensions. Terminal.

---

### All patterns found by pure PrefixSpan (min_length ≥ 2, min_support ≥ 2):

```
Pattern                                         Support
──────────────────────────────────────────────────────
[0,1]   C:Diabetes → M:Metformin               4
[0,2]   C:Diabetes → P:HbA1c                   3
[0,3]   C:Diabetes → M:Insulin                 2
[0,5]   C:Diabetes → P:ECG                     2
[0,1,2] C:Diabetes → M:Metformin → P:HbA1c    3
[0,1,3] C:Diabetes → M:Metformin → M:Insulin  2
[0,1,5] C:Diabetes → M:Metformin → P:ECG      2
[1,2]   M:Metformin → P:HbA1c                  4
[1,3]   M:Metformin → M:Insulin                2
[1,5]   M:Metformin → P:ECG                    3
[1,2,5] M:Metformin → P:HbA1c → P:ECG        2
[2,5]   P:HbA1c → P:ECG                        2
[4,5]   C:Hypertension → P:ECG                 2
```

With `min_length = 3`, only patterns of length ≥ 3 survive:
```
[0,1,2] C:Diabetes → M:Metformin → P:HbA1c    3
[0,1,3] C:Diabetes → M:Metformin → M:Insulin  2
[0,1,5] C:Diabetes → M:Metformin → P:ECG      2
[1,2,5] M:Metformin → P:HbA1c → P:ECG        2
```

These four patterns are what pure PrefixSpan (with min_length=3) returns, ranked by support. This is what you'd get from the algorithm alone, without any of our improvements.

---

## 6. Trace 2 — Full Pipeline (All Improvements)

We use the same 6-patient dataset but now trace through every step of our implementation.

### 6.1 Preprocessing

**Input raw events** (before any filtering):

```
Patient | event_date | item
--------|------------|----------------------------
P1      | 2022-01-10 | C:Diabetes
P1      | 2022-01-10 | M:Metformin
P1      | 2022-03-15 | P:HbA1c
P1      | 2022-06-01 | M:Insulin
P2      | 2021-11-01 | C:Diabetes
P2      | 2021-11-01 | M:Metformin
P2      | 2022-02-10 | P:HbA1c
P2      | 2022-02-10 | C:Medication review due   ← blacklisted
P3      | 2022-04-01 | C:Hypertension
P3      | 2022-04-05 | M:Metformin
P3      | 2022-05-01 | P:HbA1c
P3      | 2022-07-15 | P:ECG
P4      | 2020-06-01 | C:Diabetes                ← old event (> WINDOW_DAYS ago)
P4      | 2022-07-01 | C:Diabetes
P4      | 2022-07-01 | M:Metformin
P4      | 2022-08-10 | M:Insulin
P4      | 2022-09-01 | P:ECG
P5      | 2022-01-05 | C:Hypertension
P5      | 2022-01-05 | M:Lisinopril
P5      | 2022-03-20 | P:ECG
P6      | 2022-02-14 | C:Diabetes
P6      | 2022-02-14 | M:Metformin
P6      | 2022-04-01 | P:HbA1c
P6      | 2022-05-15 | P:ECG
```

**Step 1: Sort** — within each patient, sort by (date, type_rank, name). On 2022-01-10 for P1: C:Diabetes (rank 0) before M:Metformin (rank 1). Already correct.

**Step 2: Blacklist** — P2's `C:Medication review due` contains "medication review due" → drop that row.

**Step 3: Rolling window** — P4's most recent event is 2022-09-01. Window cutoff = 2022-09-01 − 730 days ≈ 2020-09-07. P4's event on 2020-06-01 is before that cutoff → dropped.

**Step 4: Consecutive dedup** — no consecutive duplicates in this dataset.

**Step 5: Cap at 25** — all patients have ≤ 4 events, so nothing is removed.

**Resulting sequences after preprocessing:**

```
P1: [C:Diabetes, M:Metformin, P:HbA1c, M:Insulin]
P2: [C:Diabetes, M:Metformin, P:HbA1c]
P3: [C:Hypertension, M:Metformin, P:HbA1c, P:ECG]
P4: [C:Diabetes, M:Metformin, M:Insulin, P:ECG]
P5: [C:Hypertension, M:Lisinopril, P:ECG]
P6: [C:Diabetes, M:Metformin, P:HbA1c, P:ECG]
```

Same as the toy dataset — the raw events were already clean-ish.

---

### 6.2 Mining Step

- `n_patients = 6`
- `abs_minsup = max(2, int(6 × 0.01)) = max(2, 0) = 2`
- `pool_size = TOP_K × OVERMINE_MULTIPLIER = 500 × 20 = 10000` (but in our tiny dataset the library will return all closed patterns, which is far fewer)
- `ps.topk(10000, closed=True)` with `minlen=3, maxlen=6`

The library returns the same 4 patterns as above (in a real run with thousands of patients there would be thousands here). Raw output sorted by support:

```
Rank | Support | Pattern
-----|---------|----------------------------------------------
1    | 3       | [0,1,2]  C:Diabetes → M:Metformin → P:HbA1c
2    | 2       | [0,1,3]  C:Diabetes → M:Metformin → M:Insulin
3    | 2       | [0,1,5]  C:Diabetes → M:Metformin → P:ECG
4    | 2       | [1,2,5]  M:Metformin → P:HbA1c → P:ECG
```

Apply `abs_minsup` floor: all 4 pass (support ≥ 2). ✓

---

### 6.3 Run-of-3 Same-Type Filter

Check each pattern for three consecutive same-type items:

```
[0,1,2] → types [C, M, P] → no run of 3 ✓
[0,1,3] → types [C, M, M] → run of 2 M's, not 3 ✓
[0,1,5] → types [C, M, P] → no run of 3 ✓
[1,2,5] → types [M, P, P] → run of 2 P's, not 3 ✓
```

All 4 patterns survive. In a real run, a pattern like `[M:Metformin, M:Insulin, M:Glipizide]` would be removed here.

---

### 6.4 GML Scoring

Compute single-item support counts from the 6 sequences:

```
Item          | Sequences containing it | single_support
--------------|-------------------------|---------------
C:Diabetes(0) | P1,P2,P4,P6            | 4
M:Metformin(1)| P1,P2,P3,P4,P6         | 5
P:HbA1c(2)   | P1,P2,P3,P6            | 4
M:Insulin(3)  | P1,P4                  | 2
P:ECG(5)     | P3,P4,P5,P6            | 4
```

`n = 6`, `log_n = ln(6) ≈ 1.792`

**Pattern `[0,1,2]` (support=3, unique_items={0,1,2}, types={C,M,P}, n_types=3):**

```
log_item_freqs for items {0,1,2}:
  item 0: ln(4) − ln(6) = 1.386 − 1.792 = −0.406
  item 1: ln(5) − ln(6) = 1.609 − 1.792 = −0.183
  item 2: ln(4) − ln(6) = 1.386 − 1.792 = −0.406

mean(log_item_freqs) = (−0.406 − 0.183 − 0.406) / 3 = −0.332

raw_gml = exp( ln(3) − ln(6) − (−0.332) )
        = exp( 1.099 − 1.792 + 0.332 )
        = exp(−0.361)
        ≈ 0.70

n_types = 3 (C, M, P)
type_bonus = 1.0 + 0.3 × (3 − 1) = 1.6

gml = 0.70 × 1.6 = 1.12
```

**Pattern `[0,1,3]` (support=2, unique_items={0,1,3}, types={C,M,M}, n_types=2):**

```
  item 0: −0.406
  item 1: −0.183
  item 3: ln(2) − ln(6) = 0.693 − 1.792 = −1.099

mean = (−0.406 − 0.183 − 1.099) / 3 = −0.563

raw_gml = exp( ln(2) − ln(6) − (−0.563) )
        = exp( 0.693 − 1.792 + 0.563 )
        = exp(−0.536)
        ≈ 0.585

n_types = 2 (C, M only — both 0 and 3 have same type... wait)
```

Wait: item 0 = C:Diabetes (type C), item 1 = M:Metformin (type M), item 3 = M:Insulin (type M). So types = {C, M} → `n_types = 2`.

```
gml = 0.585 × (1.0 + 0.3 × (2−1)) = 0.585 × 1.3 = 0.76
```

**Pattern `[0,1,5]` (support=2, unique_items={0,1,5}, types={C,M,P}, n_types=3):**

```
  item 0: −0.406
  item 1: −0.183
  item 5: ln(4) − ln(6) = −0.406

mean = (−0.406 − 0.183 − 0.406) / 3 = −0.332

raw_gml = exp( ln(2) − ln(6) − (−0.332) )
        = exp( 0.693 − 1.792 + 0.332 )
        = exp(−0.767)
        ≈ 0.465

gml = 0.465 × 1.6 = 0.744
```

**Pattern `[1,2,5]` (support=2, unique_items={1,2,5}, types={M,P,P}, n_types=2):**

```
  item 1: −0.183
  item 2: −0.406
  item 5: −0.406

mean = (−0.183 − 0.406 − 0.406) / 3 = −0.332

raw_gml = exp( ln(2) − ln(6) − (−0.332) )
        = exp(−0.767)
        ≈ 0.465

gml = 0.465 × 1.3 = 0.605
```

**GML ranking:**

```
Rank by GML | GML  | Support | Pattern
------------|------|---------|----------------------------------
1           | 1.12 | 3       | C:Diabetes → M:Metformin → P:HbA1c
2           | 0.76 | 2       | C:Diabetes → M:Metformin → M:Insulin
3           | 0.744| 2       | C:Diabetes → M:Metformin → P:ECG
4           | 0.605| 2       | M:Metformin → P:HbA1c → P:ECG
```

The reranking didn't change the order here (in a real run it dramatically reshuffles thousands of patterns, often elevating rare but informative combinations over common but predictable ones).

---

### 6.5 Post-Mine Closedness Filter

Check for dominated patterns at equal support:

**At support=3**: only `[0,1,2]` → not dominated (no other pattern with support=3 that extends it).

**At support=2**: patterns `[0,1,3]`, `[0,1,5]`, `[1,2,5]`.

Check `[0,1,3]`: is there a pattern with same support=2 that is longer and contains all of {0,1,3} as a subsequence? Check `[0,1,5]` (items={0,1,5}) and `[1,2,5]` (items={1,2,5}). Neither contains item 3. Not dominated. ✓

Check `[0,1,5]`: is there a pattern with support=2 that is longer and contains {0,1,5} as a subsequence? Check `[0,1,3]` (items={0,1,3}): doesn't contain 5. Check `[1,2,5]` (items={1,2,5}): doesn't contain 0. Not dominated. ✓

Check `[1,2,5]`: Check `[0,1,5]` (items={0,1,5}): items of `[1,2,5]` are {1,2,5}, but `[0,1,5]` doesn't contain item 2. Not dominated. ✓

All 4 patterns survive closedness filter.

---

### 6.6 Sort by GML and Apply Deduplication

Pool sorted by GML descending:
```
1. [0,1,2] gml=1.12  items={0,1,2}
2. [0,1,3] gml=0.76  items={0,1,3}
3. [0,1,5] gml=0.744 items={0,1,5}
4. [1,2,5] gml=0.605 items={1,2,5}
```

**Greedy Jaccard deduplication** (threshold=0.80):

Start with empty `chosen`.

**Candidate `[0,1,2]`** — chosen is empty, no similarity to check. Accept. `chosen = {[0,1,2]}`.

**Candidate `[0,1,3]`** — compare with `[0,1,2]`:
- Intersection: {0,1,2} ∩ {0,1,3} = {0,1}, size=2
- Union: {0,1,2,3}, size=4
- Jaccard = 2/4 = 0.5 < 0.80 ✓

Accept. `chosen = {[0,1,2], [0,1,3]}`.

**Candidate `[0,1,5]`** — compare with `[0,1,2]`:
- Intersection: {0,1,2} ∩ {0,1,5} = {0,1}, size=2
- Union: {0,1,2,5}, size=4
- Jaccard = 2/4 = 0.5 < 0.80 ✓

Compare with `[0,1,3]`:
- Intersection: {0,1,3} ∩ {0,1,5} = {0,1}, size=2
- Union: {0,1,3,5}, size=4
- Jaccard = 2/4 = 0.5 < 0.80 ✓

Accept. `chosen = {[0,1,2], [0,1,3], [0,1,5]}`.

**Candidate `[1,2,5]`** — compare with `[0,1,2]`:
- Intersection: {0,1,2} ∩ {1,2,5} = {1,2}, size=2
- Union: {0,1,2,5}, size=4
- Jaccard = 2/4 = 0.5 < 0.80 ✓

Compare with `[0,1,3]`:
- Intersection: {0,1,3} ∩ {1,2,5} = {1}, size=1
- Union: {0,1,2,3,5}, size=5
- Jaccard = 1/5 = 0.2 < 0.80 ✓

Compare with `[0,1,5]`:
- Intersection: {0,1,5} ∩ {1,2,5} = {1,5}, size=2
- Union: {0,1,2,5}, size=4
- Jaccard = 2/4 = 0.5 < 0.80 ✓

Accept. `chosen = {[0,1,2], [0,1,3], [0,1,5], [1,2,5]}`.

In a real run with 10,000 candidates, many would fail the Jaccard check and be dropped.

---

### 6.7 Diversity Caps

**Prefix counts** (first item of each chosen pattern):
- Item 0 (C:Diabetes): `[0,1,2]`, `[0,1,3]`, `[0,1,5]` → count=3 (< MAX_PER_PREFIX=6 ✓)
- Item 1 (M:Metformin): `[1,2,5]` → count=1 ✓

**Suffix counts** (last item):
- Item 2 (P:HbA1c): `[0,1,2]` → count=1 ✓
- Item 3 (M:Insulin): `[0,1,3]` → count=1 ✓
- Item 5 (P:ECG): `[0,1,5]`, `[1,2,5]` → count=2 ✓

**Dental check**: None of these patterns contain dental keywords. `dental_count=0`.

All 4 pass. In a real Synthea dataset, the 16th pattern that starts with "Fluoride treatment" would be dropped because `dental_count` would already be at 15.

---

### 6.8 Final Output

```
Rank | Support | GML  | Pattern
-----|---------|------|-----------------------------------------------
1    | 3       | 1.12 | C:Diabetes -> M:Metformin -> P:HbA1c
2    | 2       | 0.76 | C:Diabetes -> M:Metformin -> M:Insulin
3    | 2       | 0.744| C:Diabetes -> M:Metformin -> P:ECG
4    | 2       | 0.605| M:Metformin -> P:HbA1c -> P:ECG
```

These 4 patterns are written to `patterns_global.txt` and then inserted into `prefix_span_pattern` (with `cluster_label=NULL` for global) and `prefix_span_patient_pattern` (with all matching patient IDs).

---

### 6.9 Patient Attribution Trace

Take pattern rank 1: `C:Diabetes → M:Metformin → P:HbA1c` (items={0,1,2}).

**Build inverted index** (already done once for all patterns):
```
posting[0] = [0, 1, 3, 5]   (P1,P2,P4,P6 — indexed as 0,1,3,5)
posting[1] = [0, 1, 2, 3, 5] (P1,P2,P3,P4,P6)
posting[2] = [0, 1, 2, 5]   (P1,P2,P3,P6)
```

**Sort unique items by rarity**: item 2 has posting length 4, item 0 has 4, item 1 has 5. Sort: [0 or 2 (both len=4), then 1 (len=5)]. Say order = [0, 2, 1].

**Intersect**:
1. Start with `candidates = set(posting[0]) = {0, 1, 3, 5}` (patient indices for P1,P2,P4,P6)
2. Intersect with `posting[2] = {0, 1, 2, 5}`: result = `{0, 1, 5}` (P1,P2,P6)
3. Intersect with `posting[1] = {0, 1, 2, 3, 5}`: result = `{0, 1, 5}` (unchanged)

**Check subsequence order** on candidates {0, 1, 5} (P1, P2, P6):
- P1 `[0,1,2,3]`: does [0,1,2] appear in order? 0 at index 0, 1 at index 1, 2 at index 2. Yes ✓
- P2 `[0,1,2]`: 0 at 0, 1 at 1, 2 at 2. Yes ✓
- P6 `[0,1,2,5]`: 0 at 0, 1 at 1, 2 at 2. Yes ✓

**Membership for rank 1**: `[patient_id(P1), patient_id(P2), patient_id(P6)]` — 3 patients. Matches support=3. ✓

---

## 7. Summary of What Each Improvement Changes

| Without improvement | With improvement |
|---------------------|-----------------|
| Ranked by raw support — most common patterns first, including trivial ones | **GML reranking**: medium-support, informative patterns rise to the top |
| `M:Metformin → M:Insulin → M:Glipizide` (all medications) included | **Run-of-3 filter**: same-type consecutive triples removed |
| Short patterns included even when a longer version with equal support exists | **Closedness filter**: dominated shorter patterns removed |
| `[A,B,C]` and `[A,B,D]` (80% same items) both included | **Jaccard dedup**: near-duplicates collapsed; only the higher-GML one kept |
| "Fluoride → HbA1c → ECG" may appear 50 times with slight variations | **Diversity caps**: first-item cap, last-item cap, dental cap |
| O(n_patterns × n_patients) subsequence checks for attribution | **Inverted index**: candidate pruning makes attribution nearly O(n_patterns × avg_posting_len) |

---

## 8. Command Line Usage

```bash
# from backend/ directory

# global mining (all patients, no cluster filter)
python app/clustering_algorithms/prefix_span/prefix_span.py

# per-cluster mining (clusters 0..3 plus -1 for outliers)
python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4
```

`--n-clusters N` tells the script to run one mining job per cluster label: `[0, 1, ..., N-1, -1]`. Each job calls `build_sequences(cluster_label=k)` which restricts the patient pool to those in `cluster_patient` with `cluster_label=k`, then mines and saves with that label as scope. The per-cluster results are saved with `cluster_label=k` in `prefix_span_pattern`, so global and per-cluster rows coexist in the same table and are distinguished by the `cluster_label` column (NULL = global, -1 = outliers, 0+ = specific cluster).
