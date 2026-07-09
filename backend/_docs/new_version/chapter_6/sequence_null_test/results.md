# Temporal-Shuffle Null Test — PrefixSpan Sequence Validation

Validation experiment for Section 6.4 (Sequence Mining Results). Answers a single
question: **do the top mined patterns encode a genuine temporal trajectory, or just
the co-occurrence of a few frequent codes?**

## Method

Each patient's event timeline is randomly permuted *in place* (`build_sequences(...,
shuffle_seed=...)`, exposed as `--shuffle`), **after** all date-based preprocessing, so
the exact same events enter mining in the real and the shuffled runs. Because the
permutation stays inside a single patient, every patient keeps the same **set** of
items, so single-item supports — and therefore the GML denominator — are unchanged.
**Only chronological order is destroyed.** Any drop in GML is attributable purely to
ordering.

- Real baseline: production files `patterns_<scope>.txt` (run of 2026-06-17, the same
  run behind the Chapter 6 result tables).
- Shuffled: `--n-clusters 4 --shuffle` at seeds **7, 42, 123**, averaged.
- Metric: mean GML of the top 10 patterns per scope; survival = patterns with GML ≥ 0.5.
- Read-only: shuffle runs never write to the database.

## Results (top-10 mean GML, averaged over 3 seeds)

| Scope                                  | real GML | shuffled GML | drop ×  | real ≥ 0.5 | shuffled ≥ 0.5 | repeated-item (A→A) in shuffled |
|----------------------------------------|:--------:|:------------:|:-------:|:----------:|:--------------:|:-------------------------------:|
| Cluster 0 (young / low-burden)         |  0.726   |    0.181     | **4.02**|     8      |    **0.0**     |               0.0               |
| Cluster 1 (women, reproductive age)    |  0.868   |    0.167     | **5.19**|    10      |    **0.0**     |               0.0               |
| Cluster 2 (hypertensive, polypharmacy) |  0.773   |    0.494     |  1.56   |    10      |      4.0       |               2.3               |
| Cluster 3 (pediatric)                  |  0.866   |    0.205     | **4.23**|    10      |    **0.0**     |               0.0               |
| Cluster -1 (oncology / renal / HF)     |  0.859   |    0.723     |  1.19   |    10      |     10.0       |               4.0               |

Per-seed shuffled means (near-identical, i.e. the null is stable, not a lucky seed):

| Scope       | seed 7 | seed 42 | seed 123 |
|-------------|:------:|:-------:|:--------:|
| Cluster 0   | 0.182  |  0.180  |  0.180   |
| Cluster 1   | 0.168  |  0.167  |  0.167   |
| Cluster 2   | 0.495  |  0.494  |  0.494   |
| Cluster 3   | 0.204  |  0.203  |  0.207   |
| Cluster -1  | 0.718  |  0.722  |  0.728   |

## Interpretation

The null test **discriminates**, and that is the point.

**Acute-care clusters (0, 1, 3) — genuine ordered trajectories.** GML collapses 4–5×
and *no* pattern survives the 0.5 threshold. Under shuffling the top spots are taken
over by generic dental co-occurrences at GML ≈ 0.18, while the real ordered pathways
vanish entirely. Order *is* the pattern here — a laceration must precede its suture.

- Cluster 0 real #1: `C:Laceration → CP:Wound care → P:Suture open wound` (gml 0.98)
  → shuffled #1: `[dental] M:sodium fluoride → P:Dental fluoride → P:Oral health education` (gml 0.19)
- Cluster 1 real #1: `C:Laceration → CP:Wound care → P:Suture open wound` (gml 0.97)
  → shuffled #1: `[dental] P:Dental fluoride → M:sodium fluoride → P:Examination of gingivae` (gml 0.18)
- Cluster 3 real #1: `C:Acute allergic reaction → P:Injection of epinephrine → M:prednisone` (gml 1.00)
  → shuffled #1: `[dental] P:Dental fluoride → P:Oral health education → M:sodium fluoride` (gml 0.22)

**Chronic-regimen clusters (2, -1) — dense co-occurrence bundles, order carries little.**
GML barely drops (1.2–1.6×) and most patterns survive. These cohorts are small and
dominated by a handful of repeated agents (chemotherapy cycles, dialysis/EPO loops,
heart-failure furosemide/prone/oxygen loops), so the same codes co-occur in almost every
patient regardless of order. Their signature is the **repeated item** (A→A→B): 2–4 of
the surviving top-10 patterns literally repeat an item, which shuffling cannot break.

- Cluster -1 real #4: `M:Cisplatin → P:Combined chemo+radiation → P:Hospice care` (gml 0.85)
  → shuffled #1: `P:Combined chemo+radiation → P:Combined chemo+radiation → M:Cisplatin` (gml 0.89, repeated item)
- Cluster 2 real dialysis loop survives: shuffled #2 `P:Renal dialysis → M:Epoetin Alfa → P:Renal dialysis` (gml 0.79)
- But a genuinely ordered diagnostic chain in cluster 2 *does* collapse: real
  `M:tropicamide → P:Slit-lamp exam → P:Diabetic retinal eye exam` falls to gml 0.32 under shuffle.

This is not a failure of the miner. An acute pathway *is* its order; a chronic regimen is
a repeated bundle where order is secondary. The null test recovers exactly that clinical
distinction, and it also confirms the GML score behaves as intended: for order-dependent
patterns it is destroyed by shuffling, and it only persists where the "pattern" is really
a co-occurrence set.

## Reproduce

```bash
# real baseline (already on disk as patterns_cluster_*.txt)
python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4

# null test (writes patterns_cluster_*_shuffled_seed<seed>.txt, no DB write)
python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4 --shuffle --shuffle-seed 7
python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4 --shuffle --shuffle-seed 42
python app/clustering_algorithms/prefix_span/prefix_span.py --n-clusters 4 --shuffle --shuffle-seed 123
```
