# MediTech Paper Plan -- "HospitAI"

## Target venue
- **MediTech Conference** (SNIMTB), proceedings published by Springer / IFMBE.
- **Format:** SPLNPROC, that is the Springer LNCS proceedings style. We use `\documentclass{llncs}`.
- **Length:** 6 to 11 pages, including title, abstract, keywords, figures, tables and references.
- **Abstract:** limited to 200 words.
- **Required statements:** Conflict of Interest, Statement of Informed Consent (if applicable), Human and Animal Rights (if applicable). These are placed at the end, before the references.
- **Other rules:** IFMBE copyright form submitted separately; paper checked for style and grammar.

## Relation to the CSSC paper
- This paper reuses the core story of the CSSC paper but goes deeper. We add the K-Prototypes objective function, the gamma weighting, the mixed-data (Gower) evaluation, the geometric mean lift derivation in log space, the diversity-selection parameters, the two-phase pattern selection, and the formal description of the SQL agent as a directed graph.
- The results section is expanded with the benchmark protocol and per-cluster pattern tables.

## Template files needed by the user
- `llncs.cls` (Springer LNCS class, from the MediTech / Springer template package).
- `splncs04.bst` (LNCS bibliography style).
Both come with the official Springer proceedings template. Drop them next to `main.tex`.

## Files (one per chapter)
| File | Section | Purpose |
|------|---------|---------|
| `main.tex` | preamble + includes | llncs class, title, abstract, keywords, includes, statements |
| `01_introduction.tex` | Introduction | problem, motivation, contributions |
| `02_related_work.tex` | Related Work | the 9 useful papers, grouped |
| `03_system_architecture.tex` | System Architecture | layered design, offline scripts, persistence, dataset |
| `04_clustering.tex` | Patient Clustering | features, K-Prototypes math, evaluation, model selection |
| `05_sequence_mining.tex` | Clinical Sequence Mining | event model, GML, diversity, two-phase selection, scopes |
| `06_ai_interpretation.tex` | AI Interpretation | LLM verbaliser, JSON outputs, SQL agent graph |
| `07_results.tex` | Results | benchmark, cluster metrics, sequence tables, ablation |
| `08_conclusion.tex` | Discussion and Conclusion | strengths, limitations, future work |
| `references.bib` | bibliography | shared with CSSC |

## Expanded chapter notes

### Clustering (deeper than CSSC)
- Objective: cost = sum of squared Euclidean on numerical + gamma * matching dissimilarity on categorical.
- Gamma role and the automatic heuristic (average spread of numerical features).
- Feature engineering: ~40 candidate features from 7 tables, final 5 numerical + 8 categorical.
- log1p on skewed counts, min-max scaling, binning of vitals with an "Unknown" bin, native categorical encoding.
- z-score outlier separation into cluster -1.
- Evaluation: Gower silhouette as primary metric, FAMD-projected Calinski-Harabasz and Davies-Bouldin as tie-breakers, feature importance via eta^2 and Cramer's V.
- Model selection: elbow on cost, 63 feature versions benchmarked, choose smallest k with all clusters cohesive.

### Sequence mining (deeper than CSSC)
- Event model: four types C/M/P/CP, one sequence per patient, fixed same-day order.
- Preprocessing: 730-day window, blacklist of administrative items, duplicate collapse, length cap of 25, integer encoding.
- PrefixSpan with closed patterns, length 3-6, support 1%, over-mining a larger pool and re-ranking.
- GML formula and log-space computation, type-diversity bonus.
- Diversity selection: same-type run filter, global closedness pass, Jaccard de-duplication, per-prefix and per-suffix caps, full-spectrum quota (two-phase selection).
- Per-cluster scope and cross-scope de-duplication.
- Storage: pattern table + patient-pattern link table, inverted-index attribution.

### AI interpretation (deeper than CSSC)
- Verbaliser principle: model only describes precomputed numbers.
- Three outputs: cluster cards, on-demand cluster/pattern JSON analysis, dashboard markdown summaries.
- SQL agent as a directed graph with nodes: classify, generate, validate, execute; bounded retries; role scoping.

## Figures and tables
1. **Fig. 1 -- Architecture** (TikZ).
2. **Fig. 2 -- Sequence-mining pipeline** (TikZ).
3. **Fig. 3 -- SQL agent graph** (TikZ).
4. **Fig. 4 -- Cluster heatmap** (`figs/cluster_heatmap.png`).
5. **Fig. 5 -- Categorical panel** (`figs/cluster_categorical.png`).
6. **Fig. 6 -- Numerical bars** (`figs/cluster_numerical.png`).
7. **Table 1 -- Final feature set** (5 numerical + 8 categorical).
8. **Table 2 -- Clustering winners per k**.
9. **Table 3 -- Sequence-pipeline parameters**.
10. **Table 4 -- v0 vs v6 ablation**.
11. **Table 5 -- Per-cluster top patterns** (cluster 2 and outliers).

## Style constraints (same as CSSC)
- B2 English, clear and simple, no rare words.
- No em-dashes. Vary sentence length so the text reads naturally.

## Citation note
- Domain citations come from the `useful` folder (9 papers).
- Huang 1998 and Pei et al. 2004 are the mandatory original-algorithm citations, kept separate in the .bib.
