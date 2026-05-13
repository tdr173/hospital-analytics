# PrefixSpan: Algorithm, Library, and Improvements

This document explains how the `prefixspan` Python library works, how the hospital-analytics mining pipeline uses it, and what every post-mine improvement does and why it exists.

---

## 1. What is PrefixSpan?

**PrefixSpan** (Prefix-Projected Sequential Pattern Mining) is an algorithm for discovering frequent *ordered* subsequences in a database of sequences. Unlike itemset mining (Apriori, FP-Growth), it preserves the order of events — making it ideal for clinical care trajectories.

### Core idea

Given a sequence database `D` and a minimum support threshold `min_sup`, PrefixSpan finds all subsequences that appear in at least `min_sup` sequences.

It works by **projection**:

1. For each frequent length-1 item `a`, build the **prefix-projected database** `D|_a` — the set of suffixes of all sequences that contain `a`, starting just after the first occurrence of `a`.
2. Recursively mine `D|_a` to discover all frequent patterns that start with `a`.

This avoids candidate generation (Apriori's bottleneck) and is memory-efficient because projected databases shrink rapidly with depth.

### The `prefixspan` PyPI library

```python
from prefixspan import PrefixSpan
ps = PrefixSpan(sequences)   # sequences: list[list[int|str]]
ps.minlen = 3
ps.maxlen = 5
results = ps.topk(k, closed=True)   # → list[(support_count, pattern)]
```

Key API:

| Method/Property | Description |
|---|---|
| `ps.topk(k)` | Returns the `k` patterns with highest support. Uses a dynamic minimum support threshold internally — much faster than `frequent()` for large `k`. |
| `ps.frequent(min_sup)` | Returns all patterns with support ≥ `min_sup`. Can return millions of patterns. |
| `ps.minlen`, `ps.maxlen` | Length bounds applied during mining. |
| `closed=True` | Only closed patterns are considered for the top-k (see §4). |

### Integer encoding

The library compares pattern items during mining. String comparisons are slow; integer comparisons are O(1). Before calling `PrefixSpan`, every unique item string is mapped to a dense integer:

```python
vocab: dict[str, int] = {}  # "C:Hypertension" → 0, "M:Metformin" → 1, ...
inv: list[str] = []          # 0 → "C:Hypertension", 1 → "M:Metformin", ...
```

After mining, each pattern (list of ints) is decoded back to strings using `inv`.

---

## 2. How Sequences Are Built

All clinical events from four tables are loaded in one `UNION ALL` query and given type prefixes:

| Prefix | Source table | Meaning |
|---|---|---|
| `C:` | `condition` | Active diagnosis |
| `M:` | `medication` | Prescribed drug |
| `P:` | `procedure` | Performed procedure |
| `CP:` | `careplan` | Active care plan |

### Processing pipeline (fully vectorised in pandas, no per-patient Python loops)

1. **Sort** events by `(patient_id, event_date, type_rank, item_name)`. The type rank (`C=0, M=1, P=2, CP=3`) makes ties deterministic.

2. **Blacklist removal** — items whose lowercased string contains any of these substrings are dropped:
   - `"assessment of health and social care needs"` — generic catch-all, ~40% of patients
   - `"medication review due"` — protocol noise
   - `"medication reconciliation"` — protocol noise

   These items appear in near-identical patterns for most Synthea patients and drown out real clinical signals.

3. **2-year rolling window** — keep only events within `WINDOW_DAYS=730` days of each patient's last recorded event. This prevents elderly patients' ancient diagnoses from dominating.

4. **Consecutive-duplicate collapse** — if a patient has the same item repeated on consecutive dates (e.g., a chronic condition recorded every encounter), keep only the first occurrence. Avoids inflated pattern lengths.

5. **Per-patient cap** — keep at most `MAX_EVENTS_PER_PATIENT=25` most recent events. Prevents patients with very long histories from distorting support counts.

6. **Group by patient** — `events.groupby("patient_id")["item"].apply(list)` → list of lists.

---

## 3. The Mining Pipeline

```
build_sequences()
    → mine_patterns()
        → PrefixSpan.topk(TOP_K * OVERMINE_MULTIPLIER, closed=True)
        → filter by abs_minsup
        → filter by run-of-3-same-type
        → GML reranking
        → post-mine closedness filter
        → greedy Jaccard dedup
    → attribute_patients()
    → save_prefix_span_results()
```

### Over-mining

`TOP_K = 500` is the final output size. Mining exactly 500 patterns by support would return the 500 most common patterns — likely dominated by a handful of ubiquitous items (e.g., every Synthea patient has a dental fluoride protocol).

Instead, mine `TOP_K × OVERMINE_MULTIPLIER = 10 000` patterns, then rerank by a diversity-aware metric (GML). Only after reranking are the top 500 selected.

### Absolute minimum support floor

```python
abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))
```

`MIN_SUPPORT_PCT = 0.01` means at least 1% of patients must contain the pattern. The `max(2, ...)` ensures trivial singletons never pass with a 1-patient cohort.

---

## 4. Post-Mine Improvements

These are the custom layers built on top of the raw `PrefixSpan` output.

### 4.1 Geometric Mean Lift (GML) Reranking

**Problem:** PrefixSpan ranks by raw support count. The most-supported patterns are dominated by items that appear in almost every patient (e.g., `C:Hypertension` in 80% of patients). A pattern `C:Hypertension → M:Lisinopril` can have high support purely because both items are common — it doesn't tell us anything we didn't already know.

**Solution:** Rank by **Geometric Mean Lift (GML)**, which measures how much more often the pattern occurs than expected if its items were statistically independent.

```
gml(pattern) = exp(
    log(support/n)
    - mean( log(support(item_i)/n) for item_i in unique_items(pattern) )
)
```

Equivalently:

```
gml = (support / n) / geometric_mean( support(item_i) / n  for each unique item )
```

- `support/n` = observed co-occurrence probability
- `geometric_mean(single_item_supports/n)` = expected co-occurrence if independent

A pattern where all items are individually rare but appear together often gets a very high GML. A pattern of universally common items gets a GML near 1 (no more informative than chance).

**Type-diversity multiplier** — patterns that span multiple event types (C+M, C+M+P, etc.) are given a bonus:

```python
gml_final = gml_raw * (1.0 + TYPE_DIVERSITY_BONUS * (n_distinct_types - 1))
```

With `TYPE_DIVERSITY_BONUS = 0.3`, a 4-type pattern (C+M+P+CP) gets a ×1.9 boost over a single-type pattern. This pushes cross-domain trajectories (e.g., `C:Diabetes → P:HbA1c → M:Insulin`) above single-domain dental permutations.

### 4.2 Run-of-3-Same-Type Filter

Patterns like `C:Caries → C:Gingivitis → C:Periodontitis` — three consecutive items of the same type — are typically Synthea protocol artefacts rather than meaningful clinical trajectories. They're dropped before GML scoring.

### 4.3 Post-Mine Closedness Filter

The `closed=True` flag in `topk()` asks the library to only count *closed* patterns during mining. However, patterns can still appear non-closed after the GML reranking step repositions them in the pool.

A pattern `P` is *dominated* by a longer pattern `Q` if:
- `len(Q) > len(P)`
- `Q` has the same support as `P`
- `P` is a non-contiguous subsequence of `Q`

In this case, `P` adds no information over `Q` — every patient containing `P` also contains `Q` with the same events. It's dropped.

**Implementation efficiency:** A full O(n²) subsequence check for 10K patterns is expensive. The filter uses frozenset subset-checking as a fast gate:
1. Group patterns by support count (only same-support pairs can dominate).
2. Check `frozenset(P).issubset(frozenset(Q))` first — O(k), no element ordering.
3. Only if the frozenset check passes, run the full two-pointer subsequence check.

### 4.4 Greedy Jaccard Deduplication

**Problem:** After GML reranking, many patterns in the top-K are near-duplicate variations of the same trajectory (e.g., `A→B→C` and `A→B→D` where C and D are both common next steps). Showing 500 near-identical patterns wastes display space.

**Solution:** Greedy dedup using **Jaccard similarity on item sets**:

```
jaccard(P, Q) = |items(P) ∩ items(Q)| / |items(P) ∪ items(Q)|
```

Patterns are accepted in GML-descending order. A pattern is rejected if its Jaccard similarity with any already-accepted pattern exceeds `JACCARD_THRESHOLD = 0.80`.

**Additional diversity caps applied during dedup:**

| Cap | Value | Purpose |
|---|---|---|
| `MAX_PER_PREFIX = 6` | max 6 patterns starting with the same item | Prevents one common condition from dominating |
| `MAX_PER_SUFFIX = 20` | max 20 patterns ending with the same item | Prevents one common terminal event |
| `MAX_DENTAL_PATTERNS = 15` | max 15 dental-majority patterns | Synthea has identical dental protocols for many patients |

A pattern is *dental-majority* if ≥ 50% of its unique items contain a dental keyword (dental, fluoride, gingiv, etc.).

---

## 5. Patient Attribution

After mining, we need to know which patients contain each pattern (for the `prefix_span_patient_pattern` junction table and for cluster-level support counts).

**Naive approach:** For each of the 500 patterns, scan all N sequences and check subsequence containment → O(500 × N × L) where L is average sequence length. With N=10K patients, this is 500M × L operations.

**Optimised approach using an inverted index:**

1. Build a posting list: `item → [list of sequence indices containing that item]`.
2. For each pattern:
   - Sort pattern items by posting list length (rarest first).
   - Intersect posting lists starting with the rarest item → candidate set shrinks rapidly.
   - Only check full subsequence order for the small candidate set.

For a pattern with 5 items each in ~5% of sequences, the candidate set after intersection is ~0.05⁵ × N ≈ 0.3 patients — the subsequence check fires almost never.

**Subsequence check** uses a two-pointer scan:

```python
def _is_subsequence(pattern, sequence):
    it = iter(sequence)
    return all(any(item == p for item in it) for p in pattern)
```

The `iter(sequence)` is shared across all pattern items, so the scan never rewinds — O(L) per check.

---

## 6. Per-Cluster Extension

### How `--n-clusters` works

Running `python prefix_span.py --n-clusters 4` mines five independent cohorts:

| Cluster label | Patients |
|---|---|
| `0` | Patients assigned cluster 0 by k-prototypes |
| `1` | Patients assigned cluster 1 |
| `2` | Patients assigned cluster 2 |
| `3` | Patients assigned cluster 3 |
| `-1` | Outliers (patients flagged by z-score filter) |

For each cohort, `build_sequences()` queries `cluster_patient WHERE cluster_label = :label` and filters the loaded events to only those patients. The entire pipeline — windowing, dedup, cap, mining, GML scoring, Jaccard dedup, attribution — runs independently on each cohort's sequences.

This means:
- Support counts are relative to the cohort size (e.g., 40% of cluster 0 patients).
- GML scores reflect within-cluster item frequencies, not population-wide ones.
- Patterns unique to a cluster surface that would be invisible in the global run (too low global support, but high within-cluster support).

### `cluster_label` in the database

The `prefix_span_pattern` table has a `cluster_label INT NULL` column:

| `cluster_label` | Meaning |
|---|---|
| `NULL` | Global mining run |
| `0, 1, 2, 3` | Cluster-specific pattern |
| `-1` | Outlier cohort pattern |

This lets global and per-cluster patterns coexist in the same table. The API defaults to returning only global patterns (`WHERE cluster_label IS NULL`). Pass `?clusterLabels=0,1` to get patterns for specific clusters.

### Re-running

Each run deletes only the rows for its specific scope before inserting new ones:

```sql
DELETE FROM prefix_span_pattern WHERE cluster_label = :label
-- or for global:
DELETE FROM prefix_span_pattern WHERE cluster_label IS NULL
```

This means you can re-run global mining without touching cluster patterns, and vice versa.

### CLI usage

```bash
# From backend/app/
python clustering_algorithms/prefix_span/prefix_span.py
# → mines global patterns (cluster_label = NULL)

python clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4
# → mines cluster 0, 1, 2, 3, -1 independently
```

Output text files are written per scope: `patterns_global.txt`, `patterns_cluster_0.txt`, `patterns_cluster_-1.txt`, etc.
