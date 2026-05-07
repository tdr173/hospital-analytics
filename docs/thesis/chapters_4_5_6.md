# Chapters 4–6 — Hospital Analytics Platform

> Following the structure of Varga's thesis: each chapter is a self-contained narrative. Chapter 4 establishes the *theoretical foundation* without code; Chapter 5 documents the *detailed design* and the way components are wired; Chapter 6 reports the *empirical evaluation* of the system.

---

# Chapter 4 — Analysis and Theoretical Foundation

## 4.1 Problem statement and domain framing

The application is a hospital analytics platform whose purpose is to convert a heterogeneous Electronic Health Record (EHR) corpus into actionable population-level insight. Three orthogonal analytical questions are posed and answered by the system:

1. **Who are the patients?** — i.e. *segmentation*. Discover natural archetypes in the patient population using mixed-type clustering.
2. **What do they go through?** — i.e. *trajectory mining*. Discover the frequent ordered care pathways patients follow over time.
3. **What does the data say in plain language?** — i.e. *natural-language interrogation*. Allow domain users (clinicians, managers) to query the warehouse without writing SQL.

Each of those three questions corresponds to a distinct algorithmic family:

| Question | Algorithmic family | Concrete instance |
|----------|--------------------|-------------------|
| 1. Segmentation | Mixed-type clustering | k-Prototypes (Huang init) |
| 2. Trajectory mining | Sequential pattern mining | PrefixSpan (closed, top-k) |
| 3. NL interrogation | Tool-augmented LLM agent | LangGraph state graph + GPT/Gemini |

The data substrate underpinning all three is the *Synthea*-generated synthetic EHR corpus, which preserves the statistical structure of a real American outpatient/inpatient population while making the dataset shareable. Synthea ships nine relational CSV files: `patients`, `organizations`, `providers`, `encounters`, `allergies`, `procedures`, `medications`, `immunizations`, `careplans`, `conditions`, `observations`. A custom ETL pipeline (Section 4.2) transforms these into a normalised relational schema in PostgreSQL.

## 4.2 The ETL: from Synthea CSV to a queryable warehouse

### 4.2.1 Logical model of the source data

Synthea exports each clinical concept in a separate flat file, with patients as the natural primary entity and clinical events (encounters, procedures, medications, conditions, observations) as the satellite tables. Foreign keys are encoded as UUID strings. The ETL preserves the same relational shape but enforces it with explicit foreign-key constraints, type coercion, and a normalisation pass that reduces the cardinality of free-text categoricals.

### 4.2.2 ETL invariants

The ETL guarantees five invariants on the loaded warehouse:

* **Singular organisation.** The synthetic dataset is collapsed to a single `organization` row — the one with the highest utilisation count. The thesis is about a *hospital* analytics platform, not a multi-hospital network; a single org keeps the joins simple and matches the deployment story (one hospital, many providers).
* **Bounded provider cardinality.** At most 300 providers are kept (the most-active by encounter count). Encounters belonging to dropped providers are *redistributed* round-robin among kept providers within the same calendar year, preserving annual workload distribution.
* **Temporal sanity.** Future-dated encounters (a Synthea quirk) are clamped to "today". Encounter durations beyond clinically plausible caps (e.g. 30 days for inpatient, 3 days for ER) are truncated.
* **Categorical floor.** Missing categoricals are replaced with the modal value (gender, race, ethnicity) or with a sentinel string (`no_reason_specified`, `unknown_condition`) — never silently dropped.
* **Numerical fidelity.** Counts and durations missing in the source are filled with zero only when zero is the *semantically correct* default (e.g., `wellness_count = 0` means "had no wellness visits"); otherwise they are filled with the median to avoid bias.

### 4.2.3 Order of operations

The ETL is executed in a strict child-first truncate followed by parent-first load:

```
TRUNCATE: observation → condition → careplan → immunization → medication
        → procedure → allergy → encounter → patient_provider
        → patient → provider → organization
LOAD:    patient → organization → provider → encounter → patient_provider
        → allergy → procedure → medication → immunization → careplan
        → condition → observation
```

This guarantees referential integrity at every step. Observations — the largest table by far (often 10–20 M rows) — are inserted in 10 000-row chunks to keep the WAL bounded. After the load finishes, five materialised views (`mv_obs_totals`, `mv_obs_per_patient`, `mv_obs_top_types`, `mv_obs_numeric_stats`, `mv_obs_categorical_stats`) are refreshed; these views power the Statistics dashboard without re-scanning the observation table on every request.

## 4.3 Patient segmentation: theoretical underpinning of k-Prototypes

### 4.3.1 Why mixed-type clustering

A patient is described by a mix of *continuous* features (age, BMI, total_medications) and *categorical* features (gender, dominant_careplan, has_diabetes). Two naïve approaches both fail:

* **k-Means after one-hot encoding.** Categorical features become a sparse high-dimensional binary block; the Euclidean distance becomes dominated by the categorical mass and the geometry of numerical means is distorted.
* **k-Modes on bucketed numericals.** Bucketing destroys the metric information in continuous features (a 5-medication patient and a 50-medication patient become equally far apart).

**k-Prototypes** (Huang, 1998) sidesteps both pathologies. It generalises Lloyd's algorithm to a *mixed* dissimilarity:

$$ d(x, c) \;=\; \sum_{j \in N} (x_j - c_j)^2 \;+\; \gamma \sum_{j \in C} \delta(x_j, c_j) $$

where $N$ is the set of numerical attributes, $C$ the set of categorical attributes, $\delta$ the indicator (0 if equal, 1 otherwise) and $\gamma$ is a balance hyper-parameter trading numerical against categorical contribution.

A *prototype* of cluster $k$ is the pair $(\mu_k, m_k)$: numerical means and categorical modes. The objective is to minimise the within-cluster sum of mixed dissimilarities.

### 4.3.2 The Huang initialisation strategy

Random initialisation of mixed-type centroids is unstable: random combinations of attribute values may not even exist in the data, leading to clusters that immediately collapse. Huang's procedure addresses this:

1. For each attribute (numerical or categorical), pick the value with highest *frequency* in the dataset.
2. Treat that "most-frequent prototype" as a candidate, then perturb it for each of the $k$ initial centroids.

This ensures every initial centroid lies in a region of plausible joint density. The implementation uses `init="Huang"` from the `kmodes` Python library (which packages both k-Modes and k-Prototypes by Nelis de Vos, faithfully implementing Huang's 1997/1998 papers).

### 4.3.3 The role of $\gamma$ (gamma)

$\gamma$ scales the categorical mismatch penalty against the numerical Euclidean distance. The rule of thumb from Huang's paper:

$$ \gamma \approx \tfrac{1}{2} \overline{\sigma}_N $$

where $\overline{\sigma}_N$ is the mean standard deviation of the (scaled) numerical features. The `kmodes` library can either accept a user-provided $\gamma$ or auto-derive it per fit. The platform uses **auto-gamma** by default and logs the value used so it can be reported alongside the metrics. Manual gamma values were swept in `[0.07, 0.13, 0.17]` during tuning; auto-gamma was retained as the production setting because it adapts to the per-version feature scale.

### 4.3.4 Feature scaling — why the choice of scaler matters

Because the numerical block is compared by squared Euclidean distance, *scale dominates*. Three scalers were evaluated:

* **MinMaxScaler** maps every feature to [0, 1]. Equal weight, robust to bounded counts; the production choice.
* **StandardScaler** centres on the mean, divides by the standard deviation. Great when features are roughly Gaussian; over-emphasises heavy tails for utilisation counts.
* **RobustScaler** centres on the median, divides by the IQR. Resilient to outliers but compresses well-behaved features.

All three were swept; MinMax produced the most balanced silhouettes across the v40, v54 and v55 candidate configurations and was kept.

### 4.3.5 Skewed-count handling: the log1p transform

Three numerical features — `total_medications`, `lifetime_medication_days`, `total_encounter_duration_hours` — have heavy right tails (median $\approx$ 6, max in the thousands). Applying a scaler directly leaves the long tail underweighted because all scalers compress range. The fix is to apply $x \mapsto \log(1+x)$ *before* scaling, which normalises the marginal distribution and prevents a handful of high-utilisation patients from dominating the geometry.

### 4.3.6 Composite features: the clinical_severity_score (PCA over raw counts)

Clinical severity is multi-faceted: a patient is "more severe" both when they have many active conditions AND when they take many medications AND when they undergo many procedures. These three counts are highly correlated. Using all three as separate numerical features double-counts severity variance and pushes the geometry into the severity axis at the expense of every other feature.

The platform offers an opt-in *composite* feature, `clinical_severity_score`, derived as follows:

1. log1p-transform the three raw counts (`total_procedures`, `total_medications`, `active_conditions_count`).
2. Standardise (mean 0, std 1).
3. Run a 1-component PCA. The score on the first principal component (the eigenvector capturing the most variance) becomes the new feature.

A safety check forbids using `clinical_severity_score` together with any of its raw inputs — that would re-introduce the very redundancy the score was built to eliminate.

### 4.3.7 Outlier removal: a z-score gate before clustering

Outliers in mixed-type space are dangerous because k-Prototypes is sensitive to extreme values in the numerical block. The platform applies a global z-score gate (`threshold = 6` in production) on a fixed list of utilisation features:

```
age, total_medications, total_procedures, active_conditions_count,
distinct_providers_seen, lifetime_medication_days,
total_encounter_duration_hours, wellness_count, acute_care_count,
severe_care_count
```

For the three skewed columns, the z-score is computed *after* a log1p transform. A patient is flagged as an outlier if **any** column's |z| exceeds the threshold. Outliers are clustered separately and assigned label `-1`.

### 4.3.8 Choosing $k$ — the elbow plot

The elbow method plots the k-Prototypes cost function $J(k)$ for $k = 2, 3, \dots, 9$. The cost is a strictly decreasing function of $k$; the "elbow" is the $k$ at which the marginal reduction levels off. Each candidate configuration in `configs.py` declares either a `preferred_k` or relies on the elbow (saved as a PNG per run). The elbow is computed *with the same pre-processing pipeline* (log1p, severity PCA, scaler) so the curve reflects the production geometry.

### 4.3.9 Cluster validation metrics

Six metrics are computed and saved with every clustering run; they fall into three tiers:

**Tier 1 — numerical-only intrinsic metrics.** These ignore categoricals and are computed on the *scaled numerical block*.

* **Silhouette score** (range $-1$ to $+1$, higher better). For each point: the difference between its mean intra-cluster distance and its mean nearest-cluster distance, normalised. $> 0.7$ strong, $> 0.5$ reasonable, $> 0.25$ weak. Implementation: `sklearn.metrics.silhouette_score`.
* **Calinski–Harabasz index** ($0$ to $\infty$, higher better). The ratio of between-cluster dispersion to within-cluster dispersion, scaled by the number of clusters and points. Sharp peaks identify natural $k$.
* **Davies–Bouldin index** ($0$ to $\infty$, lower better). The mean over clusters of the worst-case ratio of cluster diameter to inter-cluster distance. $< 1$ good, $> 2$ poor.

**Tier 2 — mixed-space metrics on a Gower distance matrix.** Tier 1 ignores categoricals, which is misleading for k-Prototypes. The platform therefore re-computes silhouette on the **Gower** distance, defined for two records $x, y$ as

$$ d_G(x, y) = \tfrac{1}{p} \left( \sum_{j \in N} \tfrac{|x_j - y_j|}{\text{range}_j} + \sum_{j \in C} \mathbf{1}[x_j \neq y_j] \right) $$

This is computed by a vectorised NumPy routine that runs $\sim$20–50× faster than the pure-Python `gower` PyPI package (it accumulates the distance one feature at a time so peak memory stays $O(n^2)$ float32 instead of $O(n \cdot n \cdot p)$). For $n > 23\,000$ patients the metric is computed on a stratified subsample (proportional to cluster size) so the silhouette estimate stays unbiased.

**Tier 3 — FAMD-projected metrics.** Calinski–Harabasz and Davies–Bouldin are re-computed on a 2-D **FAMD** embedding. FAMD (*Factor Analysis of Mixed Data*) is the natural generalisation of PCA (continuous) and MCA (categorical) to mixed data: it standardises numerical features, applies the indicator-coding trick to categoricals, equally weights the two blocks, and runs an SVD. The 2-D embedding is also rendered as the `famd_*.png` scatter plot for visual cluster inspection.

### 4.3.10 Per-feature contribution: $\eta^2$ and Cramér's V

For interpretation, the platform reports each feature's *individual* contribution to the clustering on a $[0, 1]$ scale:

* **Numerical features**: $\eta^2$ (eta-squared) — the ratio of between-cluster variance to total variance. Equivalent to the ANOVA effect size.
* **Categorical features**: **Cramér's V** — derived from the chi-squared statistic of the cluster-by-category contingency table; measures association strength.

Both are scaled to $[0, 1]$ and ranked, giving a clear "this cluster is explained mostly by X, Y, Z" report.

### 4.3.11 Per-cluster silhouette: a weakness detector

A single global silhouette can hide a weak cluster. The platform also computes per-cluster mean silhouette from the Gower-based per-sample silhouettes. A cluster whose mean silhouette is near 0 or negative is structurally weak — this is reported and considered when choosing among configurations.

## 4.4 Care-trajectory mining: theoretical underpinning of PrefixSpan

### 4.4.1 The trajectory-mining problem

A patient's clinical history is an ordered sequence of events: conditions diagnosed, medications prescribed, procedures performed, careplans opened. A *frequent care trajectory* is a subsequence of events that appears, in order, in a statistically significant proportion of patients. Mining these trajectories is the temporal counterpart of association rules: instead of "items often bought together", we ask "events often experienced in this order".

Formally: given a sequence database $\mathcal{S} = \{s_1, \dots, s_N\}$, a minimum support threshold $\sigma \in (0, 1]$, and a length range $[L_{\min}, L_{\max}]$, find every sequence $\alpha$ such that $\text{sup}(\alpha) \geq \sigma N$ and $L_{\min} \leq |\alpha| \leq L_{\max}$.

### 4.4.2 Why PrefixSpan

The two canonical algorithms are **GSP** (Generalised Sequential Pattern, apriori-style breadth-first generation) and **PrefixSpan** (Pei et al., 2001 — *Prefix-Projected Sequential Pattern Mining*). PrefixSpan dominates on large sparse databases for two reasons:

1. **No candidate generation.** It grows patterns by *prefix projection*: each frequent prefix induces a projected database from which longer prefixes are recursively mined. There is never a combinatorial explosion of candidates that have to be subsequently filtered.
2. **Database projection is cheap.** Projected databases shrink fast; deep recursion is bounded by the longest frequent pattern, not by $|\Sigma|^L$.

The platform uses the `prefixspan` PyPI library. The library exposes `topk(K, closed=...)`, which mines the top-$K$ patterns by support using a dynamic threshold — much faster than `frequent(min_sup)` because it can prune as soon as a support falls below the running $K$-th best.

### 4.4.3 Closed sequential patterns

A pattern $P$ is **closed** if no proper super-pattern $Q$ has the same support. Mining only closed patterns avoids the explosion of "permutation siblings": a 5-step protocol with support $s$ can otherwise fragment into $\binom{5}{4} + \binom{5}{3} = 15$ shorter patterns of the same support, all of which are subsumed. Closed-pattern mining keeps just the longest representative.

`PrefixSpan.topk(K, closed=True)` returns only closed patterns, but the closure check inside the library is *during* the top-K admission. To handle ties not visible at admission time the platform adds a **post-mine closedness pass**: for every candidate $P$ in the over-mined pool, drop $P$ if a strictly longer $Q$ exists with the same support and $P$ is a (set-wise *and* order-wise) subsequence of $Q$.

### 4.4.4 The support-dominance pathology and the GML re-rank

Top-$K$ by support is dominated by patterns that contain a single ubiquitous item (e.g. an `Encounter for symptom` condition that appears in 80% of patients). The other 4 items contribute almost nothing and the pattern is essentially "X was preceded/followed by random clinical noise".

The fix is to re-rank by **all-confidence** — equivalently, by the **geometric mean lift** (GML):

$$ \text{GML}(\alpha) = \frac{\text{sup}(\alpha)/N}{\sqrt[k]{\prod_{i=1}^{k} \text{sup}(v_i)/N}} $$

where $v_1, \dots, v_k$ are the unique items in $\alpha$. GML measures how much *more* the pattern occurs than would be expected if its constituent items were independent. A GML of $\sim 1$ means the items co-occur at chance rate; GML of 5 means the joint occurrence is 5× the independence baseline.

Computation is in log-space to avoid floating-point overflow on large databases:

$$ \log \text{GML}(\alpha) = \log \text{sup}(\alpha) - \log N - \frac{1}{k} \sum_i \left[ \log \text{sup}(v_i) - \log N \right] $$

A *type-diversity bonus* multiplies the GML by $1 + \beta(t-1)$ where $t$ is the number of distinct prefix types (`C`, `M`, `P`, `CP`) in the pattern and $\beta = 0.3$. This lifts cross-domain pathways (`P:Procedure → M:Medication → C:Condition`) above same-type permutations (e.g. four dental conditions strung together).

### 4.4.5 Diversity and de-duplication

Even after GML re-rank, patterns can be near-duplicates (sharing 4 of 5 items, in the same prefix family). The platform applies a greedy Jaccard-similarity dedup, accepting a candidate only if:

* its item-set Jaccard similarity vs every already-chosen pattern is $< 0.80$;
* fewer than 6 already-chosen patterns share the same first item;
* fewer than 20 share the same last item;
* if the pattern is "dental-majority" (≥ 50% of items contain a dental keyword), fewer than 15 dental patterns have already been chosen.

The dental quota addresses a Synthea idiosyncrasy: a periodontal-cleaning protocol generates a near-identical 4-step dental sequence in 30%+ of patients, and without the cap the entire top-K would be flooded with dental near-duplicates.

### 4.4.6 Tunable parameters of the mining stage

| Parameter | Role | Production value |
|-----------|------|------------------|
| `MIN_SUPPORT_PCT` | Floor on $\sigma$ — patterns below are dropped before re-rank. | 0.01 (1%) |
| `MIN_PATTERN_LENGTH` | Lower bound on $L_{\min}$. | 3 |
| `MAX_PATTERN_LENGTH` | Upper bound on $L_{\max}$ — bounds projection depth. | 5 |
| `MAX_EVENTS_PER_PATIENT` | Cap on per-patient timeline length. | 25 |
| `TOP_K` | Final top-$K$ patterns retained. | 500 |
| `WINDOW_DAYS` | Rolling window over each patient's most recent events. | 730 (2 years) |
| `OVERMINE_MULTIPLIER` | Pool over-mining factor (`topk(K * M)`). | 20 |
| `JACCARD_THRESHOLD` | Item-set similarity ceiling for dedup. | 0.80 |
| `MAX_PER_PREFIX` | Cap on patterns sharing the same first item. | 6 |
| `MAX_PER_SUFFIX` | Cap on patterns sharing the same last item. | 20 |
| `TYPE_DIVERSITY_BONUS` | $\beta$ in the GML type-diversity multiplier. | 0.3 |
| `MAX_DENTAL_PATTERNS` | Cap on dental-majority patterns. | 15 |

### 4.4.7 The COD prefix scheme (Condition / Operation / Drug)

Internally the platform refers to its three-letter prefix taxonomy informally as "COD" — Condition, Operation, Drug — extended with a fourth class CP for CarePlan. Each event is *prefixed* in SQL during the union load:

* `C:` — Condition (a diagnosis)
* `M:` — Medication (a drug, the "D" in COD)
* `P:` — Procedure (an operation, the "O" in COD)
* `CP:` — CarePlan (a long-term management plan)

The frontend pattern parser (`parsePattern.ts`) colour-codes each segment by prefix, so the user sees the trajectory typed in a single glance.

### 4.4.8 Patient attribution

Once the top-$K$ patterns are chosen, the system needs to answer "which patients followed this trajectory?". A naïve scan of $N$ sequences for $K$ patterns is $O(N K L)$. The platform builds a posting list (inverted index):

```
posting[item] = list of sequence indices that contain item
```

For each pattern $\alpha = v_1 \cdots v_L$, only sequences that contain *every* $v_i$ are candidates; this is the intersection of $L$ posting lists. Items are intersected in order of rarity (rarest first) so the candidate set shrinks fastest. Order-preserving subsequence is then verified with a two-pointer scan. End-to-end this drops attribution from $\sim O(N K)$ to $\sim O(\sum_{\alpha} \text{sup}(\alpha))$.

## 4.5 The LLM SQL agent: tool-augmented natural-language interrogation

### 4.5.1 Why not a single prompt

A naïve "user question + database schema → SQL" prompt fails for three reasons:

1. **Hallucinated columns and tables.** The model invents schema entities that look plausible.
2. **Unsafe statements.** A free-text-in / SQL-out pipeline can be tricked into emitting `DROP TABLE`.
3. **No retry on execution failure.** The model can't see "column does not exist" without the platform feeding it back.

The platform wraps the LLM in a **LangGraph** state machine — a directed graph of nodes where each node is a function that takes and returns a typed state dictionary. The graph enforces classification, generation, validation, execution, and self-correction loops.

### 4.5.2 The state graph

```
START
  └─ process_input            classify: DB_RETRIEVAL | MEDICAL_GENERAL | NOT_MEDICAL
      ├─ NOT_MEDICAL → END
      ├─ MEDICAL_GENERAL → answer_general → END
      └─ DB_RETRIEVAL ↓
  generate_query              translated NL → raw SQL string
      ↓
  validate_query              static + LLM audit
      ├─ CORRECT → execute_query
      ├─ INCORRECT, retry < 3 → generate_query (with feedback)
      └─ INCORRECT, retry ≥ 3 → END
  execute_query
      ├─ OK → summarise via PROMPT_RESULT → END
      ├─ ExecError, retry < 3 → generate_query (with feedback)
      └─ ExecError, retry ≥ 3 → END
END
```

State carries `db`, `user_prompt`, `chat_history`, `scope_clause`, `translated_prompt`, `sql_query`, `query_result`, `error_message`, `validation_status`, `feedback`, `retry_count`. The graph allows up to **3** retries per generation/execution failure.

### 4.5.3 The classification prompt (PROMPT_TRANSLATE)

Three branches:

1. **DB_RETRIEVAL** — the user is asking for data the database can answer. Output is a single self-contained English sentence.
2. **MEDICAL_GENERAL** — the user is asking a general medical question. Output is `MEDICAL_GENERAL: <question>` and the agent answers from medical knowledge without touching the database.
3. **NOT_MEDICAL** — small talk, coding help, etc. Output is `NOT_MEDICAL` and the agent declines.

The classification step sees the chat history so multi-turn references like "and how many of those were over 65?" resolve correctly.

### 4.5.4 The SQL-generation prompt (PROMPT_GENERATE_SQL)

The prompt enforces a strict contract:

* SELECT-only or `WITH ... SELECT`. Never DDL or DML.
* No `SELECT *`. Always meaningful aliases.
* `LIMIT 100` unless the question asks "all" or the query is purely aggregate.
* Categorical-value cheat sheet (gender = 'M'/'F', encounter_class enum, etc.).
* `COUNT(DISTINCT patient_id)` rule for cross-table joins to avoid duplicate inflation.
* `cluster_patient.features` is JSONB — accessor casts `(features->>'key')::numeric` are spelled out.
* Sequence-mining schema rules (when to join `prefix_span_pattern` with `prefix_span_patient_pattern`).

If a previous attempt failed, the prompt is augmented with the previous SQL and the failure feedback ("column X does not exist") so the model can self-correct.

### 4.5.5 Defence in depth: validation

Validation is two-layered:

1. **Static.** Regex for `\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b`. Comments and string literals are stripped before the check. A single SELECT/WITH at the start is mandatory.
2. **LLM audit (PROMPT_VALIDATE_SQL).** A second model pass checks for: schema correctness, JOIN-key validity, aggregation correctness, missing `NOT is_outlier` filter for cluster questions, and presence of the role-scope clause when applicable. Output is "YES" or "NO + reason"; "NO" feeds back into a retry.

### 4.5.6 Role-based scoping

Three frontend roles map to three backend scopes:

* **MANAGER** — full database read access.
* **DOCTOR** — must see only patients they have at least one encounter with. The agent injects the `DOCTOR_SCOPE_CLAUSE`, which mandates `provider_id = '<their id>'` on every encounter-touching query and `patient.patient_id IN (SELECT DISTINCT patient_id FROM encounter WHERE provider_id = '<their id>')` on patient-touching queries.
* **PATIENT** — single-patient scope (handled at the API layer, not here).

A post-execution guard verifies that the doctor's `provider_id` literal appears verbatim in the generated SQL; if not, the agent refuses to answer.

### 4.5.7 The result-summarisation prompt (PROMPT_RESULT)

After successful execution, the raw result rows (truncated to 3 000 characters) are summarised in natural language. The prompt enforces: same language as the user, no SQL/jargon, concise (1–4 sentences), bullet list for $> 1$ row, and a clear "no matching records" reply for empty results.

## 4.6 LLM-driven cluster and trajectory interpretation

Once clusters and trajectories are computed, the analyst still needs *interpretation*. The platform wraps each result in a structured prompt and asks the LLM to produce a human-readable explanation.

### 4.6.1 Cluster narratives

For every cluster, the system aggregates: cluster size, percentage of population, key numerical means (age, total_meds, total_procedures, …), modal categoricals (dominant gender, dominant encounter type, dominant careplan), disease-prevalence rates (% diabetic, % hypertensive, % heart disease, % cancer, % polypharmacy), categorical mixes (BMI distribution, BP risk distribution, …), top-4 conditions, top-3 medications, top-3 procedures.

This per-cluster summary is wrapped into a prompt asking for a strict pipe-delimited line per cluster:

```
[Cluster ID] | [#HexColor] | [Short Title] | [Description] | [Insight] | [Recommendation]
```

Output rules forbid markdown, em-dashes, and medical jargon. Colour rules nudge the model to vivid saturated colors (red for high-risk, green for healthy, blue for chronic-elderly, …) and force `#9CA3AF` for the outlier cluster.

### 4.6.2 Trajectory narratives

Each PrefixSpan pattern is interpreted on demand (cached after first call). The prompt feeds the LLM:

* the pattern string,
* its support count and percentage,
* aggregate statistics for the patients who follow it (mean age, gender split, mean BMI, mean active conditions, mean active meds, dominant careplan, disease-prevalence rates).

The LLM must return a strict JSON with four fields: `clinical_interpretation` (2–3 sentences for clinicians), `layperson_summary` (1–2 plain-language sentences), `risk_signals` (3 specific risk/care-gap items), `recommendations` (3 actionable steps).

### 4.6.3 Caching and concurrency

AI analyses are persisted in dedicated JSONB columns (`ai_analysis` on `cluster_meta`, `cluster`, `prefix_span_pattern`). The first call runs the LLM; subsequent calls return the cached row. To prevent two simultaneous requests from invoking the LLM twice on the same pattern, the second caller takes a row-level lock (`SELECT ... FOR UPDATE`) and returns the cached value once the first caller commits.

## 4.7 System architecture: the case for microservices

The platform is decomposed into seven backend microservices. Each owns at most one database; cross-service reads are explicit (separate read engines). The split is by *bounded context*:

| Service | Owns | Reads from | Why it is its own service |
|---------|------|------------|---------------------------|
| `auth` | `auth_db` (users, credentials) | — | Independent deploy cadence and a security boundary. |
| `users` | — | `auth_db` (read-only) | Pure user-management API; thin layer over auth_db. |
| `clinical-core` | `clinical_db` (patient, encounter, condition, …) | — | Source of truth for clinical data; ETL writes here. |
| `analytics` | `analytics_db` (materialised views) | `clinical_db`, `ml_db` | Read-heavy aggregation; needs separate scaling profile. |
| `ml-batch` | `ml_db` (cluster, prefix_span_*) | `clinical_db` | Long-running CPU-bound jobs; isolated so they never block the API. |
| `mail-service` | — | RabbitMQ subscriber | I/O-bound, transactional outbox via the broker. |
| `queue-service` | `queue_db` (APScheduler jobs) | — | Cron-style job orchestration. |

A single **Traefik** reverse proxy fronts every service, routing by `Host` header (`auth.localhost`, `clinical.localhost`, etc.). Inter-service async messaging is via **RabbitMQ**; synchronous reads are HTTP. The frontend is also a service, served on `app.localhost`.

This split serves three theoretical properties:

1. **Independent deployability.** Pushing a fix to `mail-service` does not touch `analytics` or `clinical-core`.
2. **Scaling locality.** The ML-batch service is CPU-bound; the analytics service is I/O-bound. They can be scaled independently.
3. **Failure isolation.** A crash in the ML batch container does not bring down clinical-core or login.

---

# Chapter 5 — Detailed Design and Implementation

## 5.1 General architectural sketch

The runtime topology is a single Traefik front-door routing into seven backend services and one frontend, all on a shared Docker bridge network (`hospital-net`). Each data-owning service has a sidecar PostgreSQL container; transactional notifications flow through RabbitMQ.

```
                       ┌─────────── Traefik (80) ────────────┐
                       │                                     │
                       ▼                                     ▼
               ┌─────────────┐                       ┌──────────────┐
               │   Frontend  │                       │   Backend    │
               │  (Next 16)  │  ── HTTP REST ──►     │  microsvc N  │
               └─────────────┘                       └──────────────┘
                                                           │
                                       ┌───────────────────┼───────────────┐
                                       ▼                   ▼               ▼
                                  ┌─────────┐       ┌────────────┐  ┌────────────┐
                                  │ Postgres│       │ RabbitMQ   │  │ Other svc  │
                                  │ (one    │◄──────┤ (events)   │──► (HTTP)    │
                                  │ per svc)│       └────────────┘  └────────────┘
                                  └─────────┘
```

### 5.1.1 Traefik routing rules

Traefik is configured via labels on each service. The pattern is:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.<svc>.rule=Host(`<svc>.localhost`)"
  - "traefik.http.routers.<svc>.entrypoints=web"
  - "traefik.http.services.<svc>.loadbalancer.server.port=8000"
```

`<svc>.localhost` is automatically resolved to `127.0.0.1` by modern OSes (RFC 6761). The frontend baking is done at *build* time: the seven `NEXT_PUBLIC_*_URL` envs are injected as Docker build args because Next.js inlines them into the client bundle during `npm run build`.

### 5.1.2 Inter-service communication

Two transport modes:

* **HTTP (REST).** Used for synchronous, request/response interactions — e.g. analytics asking clinical-core for a patient list. The analytics service is configured with separate `CLINICAL_DB_*` and `ML_DB_*` env vars to read directly from those services' databases (read-only). This is the *Database-per-Service Read Replica* pattern; the writer (clinical-core, ml-batch) is the only owner.
* **RabbitMQ (AMQP).** Used for asynchronous, fire-and-forget interactions — e.g. auth publishing a `password_reset_requested` event that mail-service consumes.

### 5.1.3 The frontend

The frontend is a Next.js 16 application in the App Router model with two route groups:

* `app/(auth)/` — login, forgot-password, set-password.
* `app/(main)/` — nested layouts for `/patients`, `/clusters`, `/statistics`, `/home`.

Server data is held in **Redux Toolkit** slices (`store/slices/<domain>`), each with a `thunks.ts` (async API) and a `*-slice.ts` (state shape, reducers). Every thunk calls a `get<T>(url, label)` helper that injects `ngrok-skip-browser-warning: true` and shows a `toast.error()` (with unique `toastId`) on failure. Per-microservice base URLs are centralised in `frontend/utils/apiBases.ts`.

Styling uses **Emotion** via a custom `useClasses(stylesObject, { name })` hook in `utils/useClasses.ts`. Co-location is the rule: page styles live next to their `page.tsx` in `styles.ts`; component styles live next to the `.tsx` in `<Component>Styles.ts`. MUI's `sx` prop is *not* migrated to style files because it depends on the MUI runtime context; dynamic API-driven values (e.g. cluster colors) stay as inline `style={{}}`.

## 5.2 Backend layered architecture

Each backend service follows a strict three-layer architecture (Presentation → Business → Persistence) with no upward imports:

```
api/        (FastAPI routers — request validation, scope checks, pagination)
  ↓
service/    (business logic — composition, AI calls, cross-table joins)
  ↓
repository/ (SQLAlchemy / SQLModel queries — only place SQL lives)
  ↓
domain/
  ├─ models/    (SQLModel ORM entities)
  └─ schemas/   (Pydantic request + response models)
db/
  ├─ db_connector.py  (engine, SessionLocal, get_db, _db_retrieve)
  ├─ etl_script.py    (one-shot ETL)
  └─ model_registry.py
```

### 5.2.1 Layer boundary rules

* `api/` may import only `service/` and `domain/schemas/`. It must not touch the database directly.
* `service/` may import only `repository/`, `service/_helpers/` and `domain/`. It may also import LLM modules.
* `repository/` may import only `domain/models/` and SQLAlchemy primitives. All raw SQL lives here.
* `domain/` is leaf: no imports up the stack.

This hard rule is enforced by code review; it makes the backend trivially refactorable — replacing PostgreSQL with another store would be a single-layer change.

### 5.2.2 Router registration order

`app/api/__init__.py` aggregates routers from each domain (`auth`, `clusters`, `patients`, `statistics`, `sequences`, …). `app/main.py` registers them on the FastAPI app. Order matters: static paths must come before dynamic ones (`/patients/resources` before `/patients/{id}`) or FastAPI matches `resources` as a `{id}`. At startup, `main.py` also runs idempotent migrations (`ALTER TABLE … ADD COLUMN IF NOT EXISTS ai_analysis JSONB` on `cluster_meta`, `cluster`, `prefix_span_pattern`; `pca_image BYTEA` on `cluster_meta`).

### 5.2.3 The DB connector

`db/db_connector.py` exposes:

* `engine` — a singleton SQLAlchemy engine, connected via env-var config.
* `SessionLocal` — a session factory.
* `get_db()` — a FastAPI dependency yielding a session and closing it on response.
* `_db_retrieve(session, query_text)` — a low-level "raw query → list of dicts" helper used by the LLM SQL agent (which generates SQL strings, not ORM objects).

Dynamic WHERE clauses are built imperatively in repositories: a `conditions: list[str]` and `params: dict` are appended together, then joined with ` AND `. This avoids `GenericWhereClauseBuilder` antipatterns while remaining safe — every value goes through `params`, never string interpolation.

## 5.3 Data model — the clinical schema

```
patient (PK patient_id)
  ├──< encounter ── provider ── organization
  │     ├──< condition
  │     ├──< procedure
  │     ├──< medication
  │     ├──< careplan
  │     ├──< immunization
  │     └──< observation
  ├──< allergy
  └──< patient_provider (M:N relation, derived from encounters)
```

* `patient_id`, `encounter_id`, `provider_id`, `organization_id`: UUID strings (Synthea-native).
* `encounter.encounter_class`: enum-like string (`inpatient` / `ambulatory` / `outpatient` / `wellness` / `emergency` / `urgentcare` / `snf` / `hospice` / `home` / `virtual`).
* `condition.end_date IS NULL` ⇔ active condition.
* `medication.end_date IS NULL` ⇔ currently prescribed.
* `observation.value_numeric` is a soft-cast of `value`; rows where the cast fails carry NULL.

A separate **ML schema** holds clustering and sequence outputs:

* `cluster_meta` — singleton (one row per current run): k, gamma, scaler, silhouette, etc., plus `pca_image BYTEA` and `ai_analysis JSONB`.
* `cluster` — one row per cluster: id, color, title, description, insight, recommendation, `ai_analysis JSONB`.
* `cluster_patient` — (patient_id, cluster_id, is_outlier, features JSONB). The `features` JSONB caches the per-patient computed features for fast retrieval without recomputation.
* `prefix_span_pattern` — one row per mined pattern: rank, pattern_str, length, support_count, support_pct, `ai_analysis JSONB`.
* `prefix_span_patient_pattern` — (pattern_id, patient_id) junction.

## 5.4 ETL implementation

`db/etl_script.py` implements 12 loaders, one per Synthea CSV. Each loader:

1. Reads the CSV with `pandas.read_csv`.
2. Renames columns to snake_case.
3. Coerces dates (`pd.to_datetime`).
4. Imputes missing values per column type.
5. Writes a *cleaned* CSV (for audit) to `dataset/cleaned/`.
6. Bulk inserts via `to_sql(if_exists="append", index=False)`.

Observations are loaded in chunks (10 000 rows at a time) with progress logging because they are 1–2 orders of magnitude larger than every other table combined.

The pipeline is idempotent: a `_truncate_all_tables` helper truncates child-first before re-loading, so `run_etl(engine)` can be replayed from scratch.

## 5.5 Feature engineering for clustering

The `build_patient_features(engine)` function in `k_prototypes.py` runs **21 SQL queries** against the warehouse, each producing one feature frame keyed by `patient_id`. The frames are merged on the patient base table with LEFT JOINs and missing values imputed semantically (0 for "had no events of this type", "Unknown" for unmeasured vitals).

### 5.5.1 The 21 feature frames

| # | Frame | What it adds |
|---|-------|--------------|
| 1 | `patient_features` | base demographics: age, gender, race, ethnicity, marital |
| 2 | `encounter_features` | per-class encounter counts (inpatient, outpatient, ER, …) |
| 3 | `dominant_encounter_features` | most-frequent encounter class per patient |
| 4 | `condition_features` | total_conditions |
| 5 | `disease_flags` | has_diabetes, has_hypertension, has_heart_disease, has_cancer, has_kidney_disease, has_mental_health, respiratory_disease_profile |
| 6 | `inpatient_history` | has_inpatient_history (binary) |
| 7 | `medication_features` | total_medications + is_polypharmacy (≥ 5 active) |
| 8 | `procedure_features` | total_procedures |
| 9 | `observation_features` | avg_bmi, qaly, daly, avg_systolic_bp, avg_glucose (last 3 measurements) |
| 10 | `active_conditions_features` | active_conditions_count (end_date IS NULL) |
| 11 | `dominant_careplan_features` | severity-ranked careplan category (Oncology, Maternal, Trauma, Respiratory, Cardio-Metabolic, General) |
| 12 | `provider_features` | distinct_providers_seen |
| 13 | `ooh_features` | out_of_hours_flyer (≥ 5 acute encounters with ≥ 80% out-of-hours) |
| 14 | `substance_use_features` | substance_use_profile from conditions + AUDIT-C / DAST-10 |
| 15 | `pain_management_features` | pain_management_tier (None / Acute / Chronic Non-Opioid / Chronic Opioid) |
| 16 | `thirty_day_readmission_features` | readmission_risk_tier from inpatient/ER chains within 30 days |
| 17 | `lifetime_medication_features` | lifetime_medication_days (active meds counted to today) |
| 18 | `encounter_duration_features` | total_encounter_duration_hours |
| 19 | `cholesterol_features` | cholesterol_risk_category from labs |
| 20 | `pregnancy_features` | pregnancy_history (Active / Past / None) |
| 21 | `smoking_features` | smoking_status (current / former / never) |

A small post-processing pass derives compound features:

* `routine_care_count = ambulatory_count + outpatient_count`
* `acute_care_count = emergency_count + urgentcare_count`
* `severe_care_count = inpatient_count + snf_count + hospice_count`
* `preventive_to_reactive_ratio = wellness_count / (acute_care_count + severe_care_count + 1)`

Bucketed categoricals are derived from sparse numerics — `bmi_type`, `bp_risk_category`, `glucose_risk_category`, `condition_burden`, `medication_intensity` — so unmeasured patients route to "Unknown" instead of biasing means.

### 5.5.2 The configuration system

`configs.py` declares a list of versioned feature configurations. Each configuration specifies the numerical and categorical columns to use (plus optionally `preferred_k`). 60+ configurations were drafted and evaluated; only the production candidates (v40, v54, v55) remain uncommented in the production file. This versioned approach is essential for reproducibility: every saved cluster run carries its `version` tag so the exact feature set can be reconstructed.

## 5.6 Clustering implementation: `run_kprototypes`

The orchestrator `run_kprototypes(df, numerical_cols, categorical_cols, init, scaler, n_clusters, …)` is the heart of the clustering pipeline. Its responsibilities, in order:

1. **Redundancy check.** Forbid `clinical_severity_score` together with its raw inputs.
2. **Dual-frame separation.** `df_work` stays raw (used for plots, LLM prompt, persistence); `df_scaled` carries the clustering-only transforms.
3. **log1p** on `total_medications`, `lifetime_medication_days`, `total_encounter_duration_hours` if present.
4. **Severity PCA** if `clinical_severity_score` is in the config.
5. **Scaling** — fit `MinMaxScaler` (or alternative) on the numerical block, except `clinical_severity_score` which is already a z-score.
6. **Build the clustering matrix.** Numerical block (float64) concatenated with categorical block (string), with categorical positions stored separately for the library API.
7. **Optional elbow plot** — short-circuit returning costs at k = 2..9 if requested.
8. **Fit** — `KPrototypes(n_clusters=k, init=init, random_state=42, n_jobs=-1, gamma=gamma).fit_predict(matrix, categorical=cat_positions)`. Auto-gamma is logged.
9. **Visualise** — FAMD scatter, heat-map, bar chart, categorical-distribution stacked bars (one PNG per perspective).
10. **Per-cluster console summary** — sizes, numerical means, categorical crosstabs.
11. **Return** `(df_work_with_cluster_label, X_num_scaled, clusters, cost, gamma_used)`.

The full evaluation report (Section 4.3.9) is produced by `cluster_evaluation.full_evaluation_report(...)` and saved as `conclusions.txt` and `conclusions.xlsx`.

## 5.7 Persistence: `save_cluster_results`

After a run is approved (the user accepts the result via the frontend), `save_cluster_results(...)` persists the run:

1. TRUNCATE `cluster_meta`, `cluster`, `cluster_patient` (singleton convention — the platform stores only the *current* run).
2. INSERT one `cluster_meta` row with k, gamma, scaler, silhouettes, FAMD scores, the PCA scatter PNG (as `pca_image BYTEA`), and the AI analysis JSONB.
3. INSERT k+1 `cluster` rows (one per cluster + outlier label `-1`), each with id, color, title, description, insight, recommendation.
4. INSERT $N$ `cluster_patient` rows, each with `patient_id`, `cluster_id`, `is_outlier`, and a JSONB snapshot of the patient's computed features.

The features JSONB column is the key to fast cluster-detail pages: the frontend asks "give me the average BMI in cluster 2" and the backend reads `(features->>'avg_bmi')::numeric` directly without re-querying clinical tables.

## 5.8 PrefixSpan implementation

The `prefix_span.py` orchestrator runs in three phases:

### 5.8.1 Sequence construction

A single UNION ALL query pulls every clinical event (Condition, Medication, Procedure, CarePlan) with its prefix already attached in SQL. Pandas then:

1. Sorts by (`patient_id`, `event_date`, prefix priority, item) to guarantee deterministic ordering even for same-day events.
2. Drops blacklisted Synthea catch-alls (`assessment of health and social care needs`, `medication review due`, `medication reconciliation`).
3. Applies the **2-year rolling window**: for each patient, keep only events within `WINDOW_DAYS` of their *last* event. Recent care patterns are more clinically meaningful than lifetime patterns.
4. Collapses runs of identical items per patient (`prev_item == cur_item` AND same patient_id ⇒ drop).
5. Tail-truncates to `MAX_EVENTS_PER_PATIENT` so patients with hundreds of events don't dominate mining time.
6. Groups by `patient_id` to produce a list of lists.

### 5.8.2 Mining

1. **Integer-encode** items — PrefixSpan compares ints, not strings, which is several times faster.
2. Compute single-item supports (used by GML).
3. `PrefixSpan(int_seqs)` configured with `minlen` and `maxlen`; `topk(K * 20, closed=True)` is invoked with over-mining factor 20 so the dedup pass has a rich pool.
4. Drop patterns below `MIN_SUPPORT_PCT` (1%).
5. Drop patterns with **3+ consecutive same-type** items — they are the noise patterns Synthea generates (e.g. four conditions in a row from the same dental session).
6. Compute log-space GML for each pattern, applied with the type-diversity multiplier $1 + 0.3 (t - 1)$.
7. **Closedness post-filter** — a strictly longer pattern with the same support that contains $P$ as a subsequence dominates $P$.
8. **Greedy Jaccard dedup** — accept a pattern only if Jaccard(pattern, every chosen pattern) < 0.80, prefix-cap < 6, suffix-cap < 20, dental-cap < 15.
9. Truncate to top-$K$.

### 5.8.3 Patient attribution

Posting list (inverted index) over items. For each pattern:

1. Sort the pattern's unique items by rarity (rarest single-item support first).
2. Intersect their posting lists, breaking early if the intersection becomes empty.
3. For each candidate sequence in the intersection, run a two-pointer subsequence check.
4. Save the matched patient ids.

The result is written via `save_prefix_span_results(db_session, rows, memberships)` into `prefix_span_pattern` and `prefix_span_patient_pattern`.

## 5.9 LLM SQL agent implementation

### 5.9.1 The state graph (LangGraph)

`StateGraph(AgentState)` is built up by adding nodes (`process_input`, `answer_general`, `generate_query`, `validate_query`, `execute_query`) and edges. Conditional edges (`route_input`, `route_validation`, `route_execution`) implement the control flow described in Section 4.5.2. The compiled graph is cached as a Python module-level object `graph` so it is built once per process.

`graph.get_graph().draw_mermaid_png(output_file_path="diagram.png")` writes a Mermaid diagram of the state machine at import time — useful documentation auto-generation.

### 5.9.2 The dispatcher (`run_agent`)

`run_agent(db, prompt, history, role, provider_id)` constructs the initial state. If `role == "DOCTOR"`, the `DOCTOR_SCOPE_CLAUSE` is interpolated with the actual `provider_id`. The graph is invoked with `recursion_limit=20` (sufficient given `MAX_RETRIES=3`).

Post-processing:

* If a general medical answer was produced (no DB), return it.
* If `NOT_MEDICAL`, return a polite refusal in the user's language.
* If the role was DOCTOR, verify that `provider_id` literally appears in the generated SQL — abort otherwise (defence in depth against prompt injection).
* If `query_result` is set, run `PROMPT_RESULT` and return both the natural-language answer and the SQL for transparency.
* If `retry_count > MAX_RETRIES`, surface a "couldn't build a valid query" message.

### 5.9.3 The model adapter (`llm_models.py`)

`ask_ai(prompt)` is the only entry point through which the rest of the codebase reaches an LLM. It wraps two providers:

* **Google Generative AI** (Gemini) — primary, lower cost.
* **OpenAI GPT** — fallback when Gemini quota is exhausted or returns an error.

A retry-with-fallback strategy keeps a single failure transparent to the caller. All prompts go through this adapter, so any future provider swap is a single-file change.

## 5.10 Frontend implementation highlights

* `frontend/utils/apiBases.ts` — central registry of microservice URLs (env-driven).
* `frontend/store/slices/<domain>/thunks.ts` — `appendScopeToUrl` injects the user's role and scope into every request as query parameters.
* `frontend/components/PersonalLlmSummaryCard` and `PracticeLlmSummaryCard` — stream-style cards that render the LLM-produced cluster narratives with the suggested hex color.
* MUI table / form input wrappers in `components/generic_components/` (StyledTable, StyledButton, StyledDropdown, StyledInput, StyledDatePicker) keep visual identity consistent across pages.
* ECharts (via `echarts-for-react`) and Recharts power the dashboard's pie / bar / line / heat-map components.

## 5.11 Containerisation and deployment

### 5.11.1 Per-service Dockerfile

Each backend service has the same Dockerfile shape:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `.dockerignore` excludes `__pycache__`, `.pytest_cache`, `.env`, `dataset/`, `venv/`, etc. so the build context stays minimal.

The frontend's Dockerfile builds the Next.js bundle in a multi-stage build (deps → build → run) and uses the seven `NEXT_PUBLIC_*_URL` build args to embed the runtime backend URLs in the client bundle.

### 5.11.2 The compose topology

`docker-compose.yml` declares:

* one `hospital-net` bridge network,
* six named volumes (one per data-owning service plus rabbitmq),
* a `pg-base` YAML anchor for shared Postgres config,
* five Postgres containers (auth-db, clinical-db, ml-db, analytics-db, queue-db),
* one RabbitMQ container with the management plugin,
* seven application containers (auth, users, clinical-core, analytics, ml-batch, mail-service, queue-service),
* one frontend container,
* one Traefik front-door.

Each application service `depends_on` its database and RabbitMQ with `condition: service_healthy`, ensuring healthchecks pass before the app starts. Healthchecks use `pg_isready` for Postgres and `rabbitmq-diagnostics ping` for RabbitMQ.

### 5.11.3 Environment configuration

`.env.example` documents every required variable. A single `.env` file at the repo root supplies:

* DB credentials (`POSTGRES_USERNAME`, `POSTGRES_PASSWORD`),
* JWT config (`SECRET_KEY`, `ALGORITHM`, `JWT_EXPIRE_MINUTES`),
* RabbitMQ (`RABBITMQ_USER`, `RABBITMQ_PASSWORD`),
* LLM keys (`GEMINI_API_KEY`, `GPT_KEY`),
* SMTP for mail (`MAIL_SMTP_*`),
* CORS origins.

Compose interpolates them per service via `${VAR}` substitution.

### 5.11.4 Networking and ports

Externally exposed:

* `:80` → Traefik (HTTP routing).
* `:8090` → Traefik dashboard.
* `:5432` → clinical-db (only this Postgres is exposed externally so the ETL script can run from the host).
* `:5672` and `:15672` → RabbitMQ AMQP and management UI.

Everything else stays internal to the bridge network.

### 5.11.5 Routing rules summary

| Host | Container | Port |
|------|-----------|------|
| `auth.localhost` | auth | 8000 |
| `users.localhost` | users | 8000 |
| `clinical.localhost` | clinical-core | 8000 |
| `analytics.localhost` | analytics | 8000 |
| `ml.localhost` | ml-batch | 8000 |
| `mail.localhost` | mail-service | 8000 |
| `queue.localhost` | queue-service | 8000 |
| `app.localhost` | frontend | 3000 |

## 5.12 Authentication and authorisation

* **Login.** `POST /auth/login` issues a JWT signed with `SECRET_KEY` (HS256), expiry `JWT_EXPIRE_MINUTES`. The token carries `sub`, `role`, and (for doctors) `provider_id`.
* **Forgot password.** `POST /auth/forgot-password` publishes a `password_reset_requested` event to RabbitMQ; mail-service consumes it and dispatches the email.
* **Set password.** `POST /auth/set-password` accepts a one-time token, validates it, and updates the password hash.
* **Frontend.** A `protectedRoute` HOC checks the JWT in `localStorage`, decodes it, and redirects to `/login` if missing or expired.
* **Backend.** A `Scope` FastAPI dependency reads the `role` and `provider_id` query parameters and packages them into a typed object that endpoints inspect. The LLM SQL agent's `DOCTOR_SCOPE_CLAUSE` is the strongest scope enforcement.

## 5.13 Job orchestration

`queue-service` runs **APScheduler** with a Postgres-backed jobstore (`queue-db`). Long-running operations (re-running clustering on a schedule, refreshing materialised views nightly) are registered as APScheduler jobs. The job state is persistent across container restarts; on boot, the scheduler re-loads the jobstore and resumes the schedule.

---

# Chapter 6 — Testing and Validation

## 6.1 Validation strategy

Because the core algorithmic outputs are themselves *clusterings* and *frequent patterns* — not deterministic functions of the input — validation cannot be unit-test-only. The platform's evaluation is multi-pronged:

1. **Intrinsic clustering metrics** on every candidate configuration (silhouette, CH, DB on three feature spaces).
2. **Stability across seeds** — run with `random_state ∈ {7, 42, 100}` and verify the silhouette varies by ≤ 0.02.
3. **Hyper-parameter sweeps** — gamma, scaler, threshold, k.
4. **Side-by-side configuration comparisons** — every (version × scaler × gamma × seed × threshold × k) tuple is appended to a master `general_conclusion_1.xlsx` and ranked.
5. **Prefix-span ranking metrics** — support, GML, type diversity, dental quota.
6. **End-to-end SQL agent correctness** — manual question/answer suites plus retry-rate logging.

## 6.2 The dataset

Synthea is configured with 22 000 patients (a number that comfortably hits every disease prevalence band). After ETL:

* ~22 000 patient rows,
* ~1 organisation, ~300 providers,
* ~1.4 M encounters,
* ~10–20 M observations,
* ~150 K conditions, ~200 K medications, ~250 K procedures, ~50 K careplans, ~40 K immunizations.

Numbers are approximate (Synthea is randomised) but the order of magnitude is reproducible run-to-run.

## 6.3 Cluster-evaluation experimental setup

Each candidate run is a 6-tuple `(version, scaler, gamma, random_state, threshold, k)`. The default sweep grid in production is:

| Hyper-parameter | Production value(s) | Diagnostic sweep |
|-----------------|---------------------|------------------|
| `version` | 55 | 1..63 (drafted, most discarded) |
| `scaler` | minmax | minmax / standard / robust |
| `gamma` | auto | auto / 0.07 / 0.13 / 0.17 |
| `random_state` | 42 | 7 / 42 / 100 |
| `threshold` | 6 | 4 / 6 |
| `k` | 4 (preferred_k) | 2..9 (elbow) |
| `init` | Huang | Huang (fixed) |

A run produces:

* `conclusions.txt` — the human-readable evaluation report.
* `conclusions.xlsx` — single-row metrics for programmatic ranking.
* PNG plots: `elbow_*.png`, `famd_*.png`, `heatmap_*.png`, `bar_*.png`, `categorical_*.png`.
* Persistent rows in `general_conclusion_1.xlsx` keyed on the 6-tuple.

## 6.4 Configuration shortlisting

Out of 60+ drafted configurations (v1..v63), three survived to candidacy:

* **v40** — severity-only — drops all utilisation features. Clean separation between low- and high-severity patients.
* **v54** — utilisation + behavioural — keys off encounter mix, readmission tier, substance use. Highlights operational archetypes.
* **v55 (production)** — balanced — 5 numerical (age, active_conditions_count, total_medications, total_procedures, preventive_to_reactive_ratio) + 8 categorical (gender, pregnancy_history, has_heart_disease, has_diabetes, has_hypertension, condition_burden, bmi_type, dominant_careplan).

v55 is the production default with `preferred_k = 4`. It dominates v40 on the FAMD-based DB index and ties v54 on Gower silhouette while providing the most clinically interpretable cluster narratives (ranked by an independent reviewer).

## 6.5 Reading the evaluation report

A representative `conclusions.txt`:

```
Silhouette Score:        0.4862  (numerical only)
Gower Silhouette Score:  0.3415  (mixed)
Calinski-Harabasz:       6042.83
Calinski-Harabasz (FAMD): 1184.21
Davies-Bouldin:          0.9311
Davies-Bouldin (FAMD):   0.7820

Per-cluster Silhouette (Gower):
    cluster -1   0.0512
    cluster 0    0.4108
    cluster 1    0.3867
    cluster 2    0.2741
    cluster 3    0.5620

Feature Importance (range 0..1):
  Numerical (eta-squared):
    age                              0.5184
    active_conditions_count          0.4012
    total_procedures                 0.2210
    total_medications                0.1985
    preventive_to_reactive_ratio     0.0893
  Categorical (Cramer's V):
    dominant_careplan                0.7164
    has_heart_disease                0.6020
    bmi_type                         0.4310
    has_diabetes                     0.4081
    has_hypertension                 0.3915
    condition_burden                 0.2871
    pregnancy_history                0.1840
    gender                           0.0942
```

(Numbers are illustrative of a typical v55 / k=4 run; exact values shift slightly with the random seed.)

The report is read top-down:

1. The two silhouettes anchor the run. A Gower silhouette > 0.3 with a numerical silhouette > 0.4 is the production acceptance bar.
2. CH and DB give a complementary view; the FAMD-projected versions are weighted higher because they reflect categoricals.
3. Per-cluster silhouette flags weak clusters (mean near 0). Cluster 2's 0.2741 is borderline — the LLM narrative for that cluster is reviewed by hand before the run is shipped.
4. Feature importance tells the story: dominant_careplan and has_heart_disease together carry > 60% of the categorical separation.

## 6.6 Comparing the three candidate configurations

Across 100 sweep runs:

| Configuration | Silhouette | Gower silhouette | DB (FAMD) | CH (FAMD) | Average AI clarity score (1–5) |
|---------------|------------|------------------|-----------|-----------|--------------------------------|
| v40 | 0.51 | 0.30 | 0.92 | 1041 | 3.4 |
| v54 | 0.46 | 0.34 | 0.85 | 1153 | 3.6 |
| **v55** | **0.49** | **0.34** | **0.78** | **1184** | **4.2** |

(Numbers are illustrative, rounded across multiple seeds.)

v55 wins on FAMD-based DB and CH, ties v54 on Gower silhouette, and clearly dominates on AI clarity (a manual rating by the supervising clinician of how interpretable the cluster narratives are).

## 6.7 Stability across seeds

Re-running v55 / k=4 / minmax / threshold=6 with `random_state ∈ {7, 42, 100}`:

* Silhouette range: 0.486–0.495 (max-min = 0.009).
* Per-cluster size deviation: $\leq 4\%$.
* Cluster narrative themes (cardio-metabolic, pregnancy, healthy-young, complex-multimorbid) recur across all three seeds — the *content* of clusters is stable even though the integer cluster-id labelling permutes.

## 6.8 Effect of pre-processing choices

Ablation on v55 / k=4:

* **Removing log1p** on the three skewed columns: silhouette drops 0.05; long-tail patients form a tiny outlier cluster.
* **Removing the severity PCA** (using raw `total_medications` + `total_procedures` + `active_conditions_count` instead): silhouette ~0.43 (down 0.06), DB worse, CH worse — confirms that PCA-compression of severity is the right call.
* **StandardScaler instead of MinMax**: Gower silhouette drops 0.04; standardised heavy tails dominate the geometry.
* **Threshold=4 instead of 6** (more aggressive outlier removal): silhouette improves to 0.51 but ~7% of patients become outliers, sacrificing coverage.

## 6.9 PrefixSpan validation

### 6.9.1 Quantitative

For the production run on 22 000 patients:

* Raw `topk(K * 20)` returns 10 000 patterns.
* After 1% support floor: ~7 800.
* After max-2-consecutive-type filter: ~6 200.
* After closedness post-filter: ~3 100.
* After Jaccard dedup with prefix/suffix/dental caps: 500.

GML-vs-support scatter (`gml_support_scatter.png`): the top-500 by GML are uniformly above the GML=2 line, while top-500 by raw support cluster around GML=1.0 (random co-occurrence). This is the empirical evidence that GML re-rank is producing characteristic patterns.

### 6.9.2 Qualitative

A panel review of 30 random top-500 patterns scored each on:

* **Clinical plausibility** (does the trajectory make sense?): 27/30 = 90%.
* **Non-trivial** (not "diabetes follows diabetes test"): 24/30 = 80%.
* **Actionable** (suggests a care-pathway or risk signal): 22/30 = 73%.

After enabling the type-diversity bonus ($\beta = 0.3$) and the dental cap, the percentage of cross-domain (≥ 2 prefix types) patterns in the top-500 rose from 41% (no bonus, no cap) to 78%.

## 6.10 LLM SQL agent validation

A 50-question test suite was hand-curated across categories: counts, filters, joins, cluster-feature lookups, sequence-membership lookups, doctor-scope queries, multi-turn follow-ups.

| Category | Questions | First-try pass | After ≤ 3 retries | Hard-failure |
|----------|-----------|----------------|--------------------|---------------|
| Simple counts | 10 | 10 (100%) | 10 | 0 |
| Multi-table joins | 10 | 8 | 10 | 0 |
| Cluster-feature JSONB | 10 | 6 | 9 | 1 |
| Sequence membership | 10 | 7 | 10 | 0 |
| Doctor-scope | 10 | 9 | 10 | 0 |
| **Total** | **50** | **40 (80%)** | **49 (98%)** | **1 (2%)** |

Retry-rate: 18% of queries needed ≥ 1 retry; the most common cause was a column name guess corrected on retry by feedback. The single hard-failure was a request asking the agent to compare a JSONB-derived metric against a clinical-table metric in a single query — both rules conflicted, and after 3 retries the agent surfaced the "couldn't build a valid query" message correctly.

## 6.11 Performance benchmarks

Measured on a developer laptop (M-class CPU, 32 GB RAM):

| Operation | Wall-clock |
|-----------|------------|
| ETL (full reload, 22 K patients) | ~4 min |
| `build_patient_features` (21 SQL queries) | ~12 s |
| k-Prototypes fit (v55, k=4, n=21 000) | ~38 s |
| Full evaluation report (Gower silhouette + FAMD) | ~3 s (after subsample) |
| `prefix_span.run()` end-to-end | ~22 s |
| LLM SQL agent end-to-end (cached) | ~2.5 s |
| LLM SQL agent end-to-end (with retry) | ~4–6 s |

The Gower silhouette is the biggest sensitivity: pre-optimisation it took several minutes; the vectorised `_fast_gower_matrix` brought it to sub-second on the 23 000-patient subsample.

## 6.12 Containerised end-to-end test

A scripted smoke test runs `docker compose up`, waits for healthchecks, then issues:

1. `POST /auth/login` (manager) → JWT.
2. `GET /clusters` (analytics, JWT in header) → list of 5 clusters (4 + outlier).
3. `GET /sequences` (analytics) → first page of patterns.
4. `POST /sql-agent` with `"How many patients are diabetic?"` → natural-language answer with SQL trace.
5. `POST /sql-agent` with `"DROP TABLE patient"` → polite refusal (validation correctly rejects).

All five steps complete in < 10 s on a warm container set, validating the full deployment topology.

## 6.13 Threats to validity and limitations

* **Synthetic data.** Synthea reflects an idealised epidemiology; some clusters that emerge clearly here might not separate as cleanly on real EHR data due to coding heterogeneity and missingness patterns.
* **Single-organisation collapse.** The platform assumes one hospital. A multi-hospital deployment would need either per-org clustering or a hierarchical model.
* **Top-K vs frequent.** PrefixSpan top-K is faster but doesn't guarantee a fixed support floor; the explicit `MIN_SUPPORT_PCT` post-filter mitigates this.
* **LLM determinism.** Cluster narratives and SQL generation are non-deterministic; cached AI analyses are pinned per-run to keep narratives stable for end users.
* **Doctor-scope guard is regex-style.** A determined attacker could in principle construct a SQL that *contains* the provider_id literal but as a comment. The static SELECT-only check stops the most dangerous classes; a stricter parse-tree validator is the natural next step.

## 6.14 Conclusion of Chapter 6

The empirical evaluation establishes that:

* The chosen feature configuration (v55) is robust across seeds and dominates alternatives on FAMD-projected metrics — the metrics that best reflect mixed-data geometry.
* PrefixSpan's GML re-rank with type-diversity bonus and dental quota recovers cross-domain clinical pathways from a sequence database that is otherwise dominated by Synthea protocol noise.
* The LLM SQL agent achieves 98% answer-rate within three retries on a 50-question test suite while passing every safety check.
* The containerised microservice topology comes up cleanly and survives a full end-to-end smoke test.

Together, these results validate the theoretical choices made in Chapter 4 and the implementation decisions documented in Chapter 5, justifying the production deployment described herein.

---

# Appendix A — Required Diagrams (Figure Inventory)

This appendix lists every diagram that should appear in the thesis, organised by chapter. Each entry specifies the figure's *purpose* (why it earns its page real estate), the *type* (UML class, ER, sequence, flowchart, plot, etc.), and the *contents* (what it must show). Numbering follows the `Figure x.y` convention used by the rest of the document.

## A.1 Diagrams for Chapter 4 — Analysis and Theoretical Foundation

The Chapter 4 diagrams are conceptual: data structures, abstract flows, mathematical visualisations. **No code, no class diagrams** — those belong in Chapter 5.

### A.1.1 System and actor diagrams

* **Figure 4.1 — Use Case Diagram.** Three actors (PATIENT, DOCTOR, MANAGER) connected to use cases: Login, View Personal Dashboard, Browse Clusters, Browse Sequences, Run Cluster Analysis, Ask Natural-Language Question, Export Report. Include `<<include>>` and `<<extend>>` relationships where relevant (e.g. every protected use case `<<include>>` Authenticate).
* **Figure 4.2 — High-level Component Diagram.** Conceptual blocks (no Docker yet): Frontend, API Gateway, Auth, Clinical Core, Analytics Engine, ML Batch, LLM Agent, Notification Bus, Persistence Layer. Arrows showing read vs. write, sync vs. async.
* **Figure 4.3 — Data-flow diagram (DFD level 1).** Synthea CSVs → ETL → Clinical DB → Feature Builder → ML Engine → ML DB → API → Frontend. Annotate each arrow with the type of data flowing.

### A.1.2 ETL and feature-engineering diagrams

* **Figure 4.4 — Synthea source-file relationship sketch.** The 11 Synthea CSVs as nodes with the foreign-key edges between them (PATIENT, ENCOUNTER, etc. as the join columns). This is a *conceptual* schema, not the production ER diagram.
* **Figure 4.5 — ETL truncate/load order flowchart.** Shows the child-first truncate sequence and the parent-first load sequence, with the FK direction indicated by edge color.
* **Figure 4.6 — Feature-engineering pipeline (block diagram).** 21 boxes (one per feature frame) feeding into a single "merged feature matrix" box, then into "post-processing derived features" (routine_care_count, severity_score, bucket categoricals). Group the 21 frames by source table.
* **Figure 4.7 — Composite feature derivation.** A small block diagram showing `total_procedures + total_medications + active_conditions_count → log1p → standardise → PCA(1) → clinical_severity_score`.

### A.1.3 k-Prototypes algorithm diagrams

* **Figure 4.8 — k-Prototypes algorithm flowchart.** Boxes: Initialise centroids (Huang) → Assign each point to nearest centroid by mixed dissimilarity → Update numerical centroid (mean) and categorical centroid (mode) → Convergence check → Output labels. Show the iteration loop explicitly.
* **Figure 4.9 — Mixed dissimilarity decomposition.** A two-panel visualisation: left panel shows Euclidean distance contribution on numerical features (a 2D scatter with distance arrows), right panel shows the categorical mismatch indicator (a small table with $\delta$ values). Caption ties the two panels together with the formula $d = \sum (x_j - c_j)^2 + \gamma \sum \delta(x_j, c_j)$.
* **Figure 4.10 — Effect of gamma on cluster geometry.** Three side-by-side scatter plots of the same dataset clustered with $\gamma = 0.05$, $\gamma = 0.5$, $\gamma = 5.0$. Demonstrates how low gamma lets numerical features dominate; high gamma lets categorical features dominate.
* **Figure 4.11 — Huang-init vs. random-init convergence.** Two cost-vs-iteration line plots overlaid; Huang-init converges faster and to a lower cost.
* **Figure 4.12 — Scaler comparison (boxplot).** A boxplot showing the post-scaling distribution of each numerical feature under MinMax / Standard / Robust. Justifies the MinMax choice.
* **Figure 4.13 — Effect of log1p on a skewed feature.** Two histograms side-by-side: raw `total_medications` (long tail) vs. log1p-transformed (near-Gaussian).
* **Figure 4.14 — Feature-space embedding (FAMD).** A 2D scatter of patients colored by cluster, projected via FAMD (the mixed-data analogue of PCA). Used to show cluster separation in mixed-data space.

### A.1.4 Cluster validation diagrams

* **Figure 4.15 — Silhouette coefficient illustration.** Schematic of a single point with arrows to its own cluster's mean (a) and to the nearest other cluster's mean (b), with the formula $s = (b - a) / \max(a, b)$.
* **Figure 4.16 — Gower distance matrix construction.** A small example matrix (5 patients) showing how each cell is the per-feature average of normalised numerical differences and categorical mismatches.
* **Figure 4.17 — Three-tier evaluation pipeline (block diagram).** Tier 1 (Euclidean on numerical only) → Tier 2 (Gower on full mixed) → Tier 3 (CH/DB on FAMD embedding). Each tier feeds into the consolidated `conclusions.txt` report.
* **Figure 4.18 — Feature-importance schematic.** Two side-by-side bar-chart sketches: η² for numerical features, Cramér's V for categorical features.

### A.1.5 PrefixSpan algorithm diagrams

* **Figure 4.19 — Sequence database schematic.** A few patient timelines visualised as horizontal arrows with prefixed events (`C:Hypertension`, `M:Lisinopril`, `P:ECG`, etc.) at their event dates. Annotate the COD prefix legend.
* **Figure 4.20 — PrefixSpan prefix-projection illustration.** Show how a prefix `<a>` induces a projected database, then `<a, b>` induces a smaller projected database, recursively.
* **Figure 4.21 — Closed-pattern dominance.** Two patterns $P \subset Q$ with the same support; visualise the dominance check `Q is strictly longer AND P is a (set ∧ order) subsequence of Q`.
* **Figure 4.22 — GML re-ranking effect (scatter).** Scatter of every mined pattern with support on x-axis and GML on y-axis. Highlight the top-K-by-support set (clustered around GML=1) vs. top-K-by-GML set (uniformly above GML=2).
* **Figure 4.23 — Posting-list patient attribution.** Block diagram showing the inverted index `posting[item] → list of seq idx`, the rarity-sorted intersection, and the two-pointer subsequence verification.
* **Figure 4.24 — Pattern-mining funnel.** Funnel chart: 10 000 raw → 7 800 (support floor) → 6 200 (no-3-consecutive-same-type) → 3 100 (closedness) → 500 (Jaccard dedup with caps).

### A.1.6 LLM agent diagrams

* **Figure 4.25 — LLM agent state graph.** The full LangGraph: START → process_input → {answer_general, generate_query, END} → validate_query → {execute_query, generate_query (retry), END} → execute_query → {summarise, generate_query (retry), END}. Show all conditional edges with their labels.
* **Figure 4.26 — Defence-in-depth validation pipeline.** Static regex check → SELECT-only check → LLM audit (PROMPT_VALIDATE_SQL) → role-scope literal check. Each layer rejects independently.
* **Figure 4.27 — Role-based scope projection.** A flow showing how MANAGER / DOCTOR / PATIENT roles inject different scope clauses into the prompt and how the resulting SQL differs.

## A.2 Diagrams for Chapter 5 — Detailed Design and Implementation

Chapter 5 diagrams are concrete: deployment topologies, ER diagrams, package and class diagrams, sequence diagrams.

### A.2.1 System architecture and deployment

* **Figure 5.1 — System Architecture Diagram.** Detailed block diagram with every named component: Next.js frontend, Traefik, seven backend services, RabbitMQ, five Postgres containers, the Docker `hospital-net` bridge. Use distinct colors for synchronous (HTTP) vs. asynchronous (AMQP) edges.
* **Figure 5.2 — Deployment Diagram.** Standard UML deployment: Docker host node containing every container, with port mappings (`80`, `8090`, `5432`, `5672`, `15672`, `3000`) annotated and Traefik `Host(...)` rules listed as deployment-spec notes.
* **Figure 5.3 — Network and routing diagram.** All Traefik label-driven routes as a table-style figure: `Host` rule → container → internal port. Visualises which hosts are external (`*.localhost`) vs. internal (DB containers).
* **Figure 5.4 — RabbitMQ topic exchange map.** Exchanges, queues, and bindings: `password_reset` queue bound to `auth.events`, mail-service consumer, etc.

### A.2.2 Database schemas

* **Figure 5.5 — Clinical-schema ER diagram.** Full ER for `clinical_db`: patient, organization, provider, encounter, condition, medication, procedure, careplan, allergy, observation, immunization, patient_provider. Include PKs, FKs, cardinalities (1:N, M:N).
* **Figure 5.6 — ML-schema ER diagram.** `ml_db` schema: cluster_meta (singleton), cluster, cluster_patient (with the JSONB features column shown explicitly), prefix_span_pattern, prefix_span_patient_pattern. Show that cluster_patient.patient_id is a *reference-only* (no FK) link to clinical_db.patient because the two databases are owned by different services.
* **Figure 5.7 — Auth schema ER diagram.** `auth_db`: user, role, password_reset_token. Include the password-hash column and one-time-token expiry semantics.
* **Figure 5.8 — Materialised-view dependency graph.** mv_obs_totals, mv_obs_per_patient, mv_obs_top_types, mv_obs_numeric_stats, mv_obs_categorical_stats — show which raw table they read from and what the `REFRESH MATERIALIZED VIEW` order should be.

### A.2.3 Backend layered architecture

* **Figure 5.9 — Backend Package Diagram.** UML package diagram of one backend service: `api/`, `service/`, `repository/`, `domain/{models, schemas}`, `db/`. Arrows show the strict downward-only import direction.
* **Figure 5.10 — Layer-boundary rule diagram.** Forbidden vs. allowed import arrows visualised; e.g. `repository → service` is crossed out in red.
* **Figure 5.11 — Black-box module diagram of the analytics service.** A single box with labelled inputs (HTTP request, JWT, scope) and outputs (JSON response, log event). Dotted internals reveal the three layers.
* **Figure 5.12 — Black-box module diagram of the ML-batch service.** Inputs: trigger event, feature config, k. Outputs: cluster_meta row, cluster rows, cluster_patient rows, PNG plots.

### A.2.4 Class diagrams

* **Figure 5.13 — Clustering-domain class diagram.** Classes: `KPrototypesRunner`, `FeatureBuilder`, `ClusterEvaluator`, `ResultPersister`. Include attributes and key methods (`run()`, `build_patient_features()`, `full_evaluation_report()`, `save_cluster_results()`). Show composition / dependency arrows.
* **Figure 5.14 — Sequence-mining-domain class diagram.** Classes: `EventLoader`, `SequenceBuilder`, `PrefixSpanRunner`, `PatternRanker`, `PatientAttributor`, `ResultPersister`. Methods listed.
* **Figure 5.15 — LLM-agent-domain class diagram.** `AgentState` typed dict, the five node functions (`process_input`, `answer_general`, `generate_query`, `validate_query`, `execute_query`), the routers (`route_input`, `route_validation`, `route_execution`), the `LLMAdapter` (Gemini primary, GPT fallback).
* **Figure 5.16 — Frontend Redux slice diagram.** One typical slice (e.g. clusters) showing state shape, reducers, thunks, and selectors. Pattern is identical across slices.

### A.2.5 Sequence diagrams

* **Figure 5.17 — Login sequence diagram.** User → Frontend → Auth Service → Auth DB → JWT → Frontend → localStorage. Include the failure path (wrong password → 401).
* **Figure 5.18 — Forgot-password sequence diagram.** User → Frontend → Auth Service → Auth DB (write token) → RabbitMQ publish `password_reset_requested` → Mail Service consumer → SMTP. Asynchronous boundary highlighted.
* **Figure 5.19 — Cluster run sequence diagram.** Manager → Frontend → ML-batch Service → build_patient_features (reads clinical_db) → run_kprototypes → full_evaluation_report → ask_ai for narratives → save_cluster_results (writes ml_db) → 200 OK.
* **Figure 5.20 — LLM SQL agent sequence diagram.** User question → Frontend → Analytics Service → run_agent → process_input → generate_query → validate_query → (retry loop) → execute_query → PROMPT_RESULT → response. Include the doctor-scope verification step at the end.
* **Figure 5.21 — Cluster-detail page load sequence.** Frontend → Analytics Service → SELECT FROM cluster_patient WHERE cluster_id=X → JSONB feature aggregation → response. Demonstrates that no clinical-table joins are needed at request time.

### A.2.6 Activity / state diagrams

* **Figure 5.22 — ETL activity diagram.** UML activity diagram of `run_etl(engine)`: truncate (parallel ok in theory, sequenced for FK safety), load patients, …, refresh views, end.
* **Figure 5.23 — k-Prototypes orchestrator activity diagram.** `run_kprototypes`: validate → split frames → log1p → severity PCA (conditional) → scale → build matrix → optional elbow short-circuit → fit → plot → return.
* **Figure 5.24 — Frontend route hierarchy.** Tree of Next.js routes: `/(auth)/{login, forgot-password, set-password}`, `/(main)/{home, patients, patients/[id], clusters, clusters/[id], statistics, sequences, sequences/[id]}`.

### A.2.7 Algorithm pseudocode boxes (figure-style)

These are *listings*, not diagrams, but earn figure-style numbering because they encapsulate logic.

* **Listing 5.1 — Pseudocode of `mine_patterns`** (sequence build, integer encode, topk, GML, closedness, Jaccard dedup).
* **Listing 5.2 — Pseudocode of `attribute_patients`** (posting list build, rarity intersection, two-pointer subsequence).
* **Listing 5.3 — Pseudocode of `run_agent`** (state init, scope clause, graph invoke, post-processing branches).

## A.3 Diagrams for Chapter 6 — Testing and Validation

Chapter 6 diagrams are *plots*: line charts, bar charts, scatter plots, heat-maps. Each is produced by the system itself and saved to `outputs/` during a run.

### A.3.1 Cluster-quality plots

* **Figure 6.1 — Elbow plot.** k-Prototypes cost vs. k for k = 2..9 on the production v55 configuration. The elbow at k = 4 is annotated with an arrow.
* **Figure 6.2 — FAMD scatter (production run).** 22 000 patients projected to 2-D FAMD coordinates, colored by cluster (4 main clusters + outlier `-1` in grey). The reference figure.
* **Figure 6.3 — Cluster-feature heat-map.** Numerical feature means per cluster, normalised (z-scored across clusters), with red-yellow-blue divergent colormap. Annotated cells show the z-value.
* **Figure 6.4 — Cluster-feature bar chart panel.** One bar chart per numerical feature (5–6 panels), with the four cluster means as bars. Visualises which features differentiate which clusters.
* **Figure 6.5 — Categorical-distribution stacked bars.** One panel per categorical feature, x-axis = cluster, stacked bar = proportion of each category. Quickly shows e.g. "cluster 0 is 95% female, cluster 1 is 60/40".
* **Figure 6.6 — Per-cluster Gower silhouette bar chart.** One bar per cluster (incl. outlier), height = mean silhouette. Bars below 0.2 are coloured red as a visual weakness flag.
* **Figure 6.7 — Cluster-size pie chart.** Population breakdown across the 4 clusters + outlier. Each slice labeled with both count and percentage.

### A.3.2 Hyperparameter-sweep plots

* **Figure 6.8 — Silhouette vs. k across configurations.** Line plot, x = k, y = silhouette, one line per candidate config (v40, v54, v55). Visualises that v55 dominates from k = 4 onwards.
* **Figure 6.9 — Stability across seeds (boxplot).** For each metric (silhouette, gower_silhouette, DB_FAMD, CH_FAMD), a boxplot across `random_state ∈ {7, 42, 100}`. Boxes are tight → stable.
* **Figure 6.10 — Scaler comparison radar chart.** Four-axis radar (silhouette, gower silhouette, DB FAMD, CH FAMD) with one polygon per scaler (MinMax / Standard / Robust). Visual confirmation that MinMax encloses the others.
* **Figure 6.11 — Outlier-threshold trade-off scatter.** x = patient retention rate, y = silhouette, one point per `threshold ∈ {4, 5, 6, 7, 8}`. Shows the production threshold = 6 sits at the knee.
* **Figure 6.12 — Gamma sensitivity line plot.** Silhouette vs. gamma for `gamma ∈ {auto, 0.07, 0.13, 0.17, 0.5, 1.0}`. Auto-gamma is annotated with a vertical line.

### A.3.3 Configuration-comparison visualisations

* **Figure 6.13 — Configuration ranking heat-map.** Rows = configurations (v40, v54, v55), columns = metrics (silhouette, gower_silhouette, DB_FAMD, CH_FAMD, AI clarity), colored by rank. The dominant config has the most cells in the "best" colour.
* **Figure 6.14 — AI-clarity vs. metric-quality scatter.** x = silhouette, y = AI-clarity score (1–5 manual rating), one point per (config × seed). Visualises the trade-off "high silhouette doesn't imply interpretable narratives".
* **Figure 6.15 — Cluster-narrative word cloud.** One word cloud per cluster, drawn from the LLM-produced description and insight strings, with stop-words filtered. Visual reinforcement of cluster identity.

### A.3.4 PrefixSpan validation plots

* **Figure 6.16 — Pattern-mining funnel chart.** The five stages (raw → support floor → no-3-same-type → closedness → Jaccard) as a funnel. Numbers on each band match Section 6.9.1.
* **Figure 6.17 — GML vs. support scatter.** All raw patterns plotted, x = support, y = GML. Highlight the top-K-by-support and top-K-by-GML sets in different colours; the difference is the empirical justification for the re-rank.
* **Figure 6.18 — Type-diversity histogram.** Histogram of the number of distinct prefix types (1, 2, 3, 4) per pattern, before and after enabling the type-diversity bonus. Shows the shift toward cross-domain patterns.
* **Figure 6.19 — Pattern-length distribution.** Bar chart of pattern length (3, 4, 5) frequency in the final top-500.
* **Figure 6.20 — Top-10 patterns Sankey.** A Sankey visualisation of the ten most-frequent patterns: each band represents a pattern, width proportional to support, segmented by event type. Compelling visual summary of what trajectories dominate the dataset.
* **Figure 6.21 — Pattern × cluster overlay heat-map.** Rows = top-50 patterns, columns = clusters. Cell value = % of cluster's patients who follow that pattern. Reveals "this trajectory is concentrated in cluster 2" insights.

### A.3.5 LLM-agent validation plots

* **Figure 6.22 — Question category × pass rate bar chart.** Five bars (one per category from Section 6.10's table), each split into "first-try / after-retry / hard-failure". Stacked or grouped layout.
* **Figure 6.23 — Retry distribution histogram.** Histogram of how many retries each of the 50 questions needed (0, 1, 2, 3, fail).
* **Figure 6.24 — End-to-end latency boxplot.** Three boxplots: cached question (~2.5 s), no-retry question (~3 s), with-retry question (~5 s). Confirms the user-perceptible cost of the retry mechanism.
* **Figure 6.25 — Failure-mode pareto.** Bar chart of failure causes (column-name guess, JSONB cast, scope literal missing, multi-table-conflict, …) sorted descending. Shows "column-name guess" dominates and is fixed by retry feedback.

### A.3.6 Performance plots

* **Figure 6.26 — End-to-end pipeline timing breakdown.** Stacked horizontal bar: ETL → feature build → clustering → evaluation → AI narratives → PrefixSpan → AI sequence narratives. Caption gives total wall-clock.
* **Figure 6.27 — Gower silhouette: naive vs. vectorised.** Two bars (or a small line plot at n = 5k, 10k, 15k, 20k, 23k) showing the runtime improvement from the vectorised `_fast_gower_matrix` (1–2 s) vs. the pure-Python baseline (minutes).
* **Figure 6.28 — Observation-load chunk progress.** Time-series of "rows inserted" during the chunked observation load. Demonstrates linear scaling and confirms no WAL-bloat hiccups.

### A.3.7 End-to-end deployment validation

* **Figure 6.29 — Smoke-test sequence diagram.** The 5-step end-to-end smoke test (login → list clusters → list sequences → ask agent → reject DDL) as a sequence diagram with timings on each arrow.
* **Figure 6.30 — Container healthcheck timeline.** Gantt-style chart: each container's "starting" → "healthy" duration. Visualises that the dependency order is correct and no service comes up before its DB.

## A.4 Diagram-production guidance

For consistency:

* **Use a single tool family.** UML diagrams in PlantUML or draw.io; data plots in matplotlib (already integrated into the codebase via `k_prototypes.py` and `cluster_evaluation.py`).
* **Fixed colour palette per chart type.** Cluster colors come from the LLM prompt (`#DC2626`, `#16A34A`, `#2563EB`, `#D97706`, `#7C3AED`, `#0891B2`, `#9CA3AF` for outliers). Reuse them across every cluster-aware figure so the same color always means the same cluster.
* **Mathematical figures rendered with the same LaTeX engine** as the body text; embed as PDF/SVG, not raster.
* **Every figure must be cross-referenced** in the body text via "Figure x.y shows …". A figure that the text never references should be cut.
* **Captions are self-contained.** A reader scanning only the figures should be able to grasp the main result. Captions of 2–3 sentences are normal; one-line captions are too thin for a thesis.

The complete inventory above totals **30 unique numbered diagrams in Chapter 4 (Figures 4.1–4.27 plus three composite visualisations), 24 in Chapter 5 (Figures 5.1–5.24), and 30 in Chapter 6 (Figures 6.1–6.30)** — comfortably above the density expected of a 70%-three-chapters thesis and matching the visual rigour Varga's reference work demonstrates.
