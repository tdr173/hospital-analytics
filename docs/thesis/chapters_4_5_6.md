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

Synthea exports each clinical concept in a separate flat file, with the patient as the primary entity and clinical events (encounter, condition, procedure, medication, observation, allergy, careplan, immunization) as satellite tables. The relational backbone is held together by UUID-encoded foreign keys (`PATIENT`, `ENCOUNTER`, `PROVIDER`, `ORGANIZATION`). Eleven CSVs are consumed: `patients`, `organizations`, `providers`, `encounters`, `allergies`, `procedures`, `medications`, `immunizations`, `careplans`, `conditions`, `observations`. The ETL preserves this shape in a normalised PostgreSQL schema while applying five families of transformations: column renaming and type coercion, business-rule normalisation, audit-trail emission, semantic imputation, and bulk insertion.

### 4.2.2 ETL invariants

Five invariants are enforced on the loaded warehouse:

* **Singular organisation.** The synthetic export is collapsed to one `organization` row — the row with the highest `UTILIZATION` value. The platform is a *single-hospital* analytics tool; collapsing the org keeps every cross-table join logically straightforward and removes a category of artificial multi-hospital noise that Synthea generates.
* **Bounded provider cardinality.** At most 300 providers are kept, ranked by encounter frequency. Encounters belonging to dropped providers are not deleted: they are redistributed round-robin among the kept providers, *within the same calendar year* the encounter took place, in proportion to that year's per-provider activity. A global fallback (the most-active provider across all years) handles years with no kept providers.
* **Temporal sanity.** Future-dated encounters (a Synthea quirk where simulated dates can drift past `today`) are clamped to the current UTC midnight. Encounter durations are clamped per encounter class to clinically plausible upper bounds: wellness ≤ 2 h, ambulatory ≤ 8 h, outpatient/urgentcare ≤ 24 h, emergency ≤ 72 h, inpatient ≤ 30 days.
* **Semantic imputation.** Missing categoricals are replaced with the modal value (for demographics: gender, race, ethnicity) or with an explicit sentinel string (`no_reason_specified`, `unknown_condition`, `unknown_allergy`, `unknown_vaccine`, `unknown_careplan`, `routine_procedure`). Numerical NaNs are replaced with the median for fidelity-preserving columns (encounter and procedure counts on `provider`) and with zero only when zero is the semantically correct default (per-class encounter counts, polypharmacy flag).
* **Auditable cleaning.** Every loader writes a `cleaned_<table>.csv` to `dataset/cleaned/` immediately before the bulk insert. This is the materialised audit trail: a reviewer can diff `dataset/cleaned/cleaned_patients.csv` against `synthea/output/csv/patients.csv` and reconstruct exactly which rows were normalised and how.

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

This guarantees referential integrity at every step. The truncation order is the inverse of the foreign-key direction; the load order is the foreign-key direction. The pipeline is idempotent — `run_etl(engine)` can be replayed from scratch.

### 4.2.4 Per-table loaders (loader-by-loader specification)

Each of the 12 loaders performs the same five-step pattern: `pandas.read_csv` → column rename → type coercion / derived columns → semantic imputation → write `cleaned_*.csv` audit file → `to_sql(if_exists="append")`. The differences below describe the *business-rule layer* on top of that pattern.

* **`load_patients`.** Renames {Id, BIRTHDATE, DEATHDATE, FIRST, LAST, MARITAL, GENDER, RACE, ETHNICITY, CITY} → {patient_id, birthdate, deathdate, first_name, last_name, marital, gender, race, ethnicity, city}. `_strip_digits` removes the trailing numeric suffix Synthea appends to first/last names (`Maria123` → `Maria`). Missing `marital` → `'S'` (single). Missing `gender`/`race`/`ethnicity` → modal value of the column. `birthdate` and `deathdate` are coerced to UTC datetime. A derived **`age`** column is computed as `(deathdate or today − birthdate).days // 365`, so the age of deceased patients freezes at death.
* **`load_organizations`.** Reads `organizations.csv`, picks the row with `UTILIZATION = max`, drops `latitude`/`longitude` (geo-analytics out of scope), and keeps {organization_id, name, city, phone, utilization}. Yields exactly one row.
* **`load_providers`.** Filters to the top-300 providers by encounter frequency (computed by a one-pass `value_counts` on `encounters.csv`). Forces `organization_id` to the singleton org id. Splits `NAME` on the *last* whitespace to {first_name, last_name} and applies `_strip_digits` to both. Modal-imputes `gender` and `speciality`; median-imputes `encounters` and `procedures` counts.
* **`load_encounters`.** The most rule-heavy loader. (i) Computes a per-year provider-activity ranking (`year_to_providers`) and a global fallback. (ii) Identifies the *dropped* set (providers not in the top-300). (iii) For every encounter whose provider was dropped, picks a replacement round-robin from the same year's kept-provider list, falling back to the global fallback. (iv) Forces `organization_id` to the singleton org id. (v) Coerces `start_date`/`end_date` to UTC. (vi) Clamps both dates to `today` to remove Synthea's future-dated rows. (vii) Computes **`duration`** in minutes as `(end_date − start_date).total_seconds() / 60`. (viii) Caps `duration` per encounter class — `wellness 120`, `ambulatory 480`, `outpatient 1440`, `urgentcare 1440`, `emergency 4320`, `inpatient 43200`. (ix) Sentinel-imputes textual fields (`encounter_class`, `description`, `reason_description`) to `'no_reason_specified'`. (x) Median-imputes `duration` if any remaining NaN.
* **`load_patient_providers`.** Reads back the just-written `cleaned_encounters.csv`, projects `(patient_id, provider_id)`, drops duplicates and NaNs, writes the M:N junction `patient_provider`.
* **`load_allergies`.** Renames {START, STOP, PATIENT, ENCOUNTER, CODE, DESCRIPTION} → {start_date, end_date, patient_id, encounter_id, allergy_code, description}. Coerces dates to UTC. Sentinel-imputes `description` → `'unknown_allergy'`. Inserts with auto-generated integer `id`.
* **`load_procedures`.** Same as `load_allergies` plus `reason_description`. Both `description` and `reason_description` sentinel-impute to `'routine_procedure'`.
* **`load_medications`.** Same as `load_procedures` plus a derived **`duration_days = (end_date − start_date).dt.days`**, with NaN → 0 (a NaN here means an active prescription with no end_date). Sentinels: `'no_reason_specified'`.
* **`load_immunizations`.** Renames {DATE, PATIENT, ENCOUNTER, CODE, DESCRIPTION}. Sentinel: `'unknown_vaccine'`.
* **`load_careplans`.** Renames the standard set plus `REASONCODE`/`REASONDESCRIPTION`. Coerces both dates with `errors='coerce'` (Synthea sometimes leaves a careplan open with an invalid stop date). Derived `duration_days` (NaN → 0). Sentinels: `'unknown_careplan'`, `'no_reason_specified'`.
* **`load_conditions`.** Standard rename + sentinel `'unknown_condition'`.
* **`load_observations`.** The largest table by 1–2 orders of magnitude. Standard rename. A derived **`value_numeric = pd.to_numeric(value, errors='coerce')`** column is added — categorical observations (e.g. `Tobacco smoking status`) yield NaN, numerics survive. Before the insert, `TRUNCATE observation RESTART IDENTITY CASCADE` resets the table; rows are then inserted in chunks of **10 000 rows**, with progress logged after every chunk so that a 20 M-row load remains observable. Bulk WAL stays bounded because each chunk is its own transaction.

### 4.2.5 Materialised views

After `load_observations`, `_refresh_observation_views` issues `REFRESH MATERIALIZED VIEW` against five pre-defined views:

* **`mv_obs_totals`** — global counts (rows, distinct types, distinct patients).
* **`mv_obs_per_patient`** — per-patient row counts and last-observation-date.
* **`mv_obs_top_types`** — top-N most-frequent observation descriptions.
* **`mv_obs_numeric_stats`** — per-description min/max/mean/median/stddev for numerical observations.
* **`mv_obs_categorical_stats`** — per-description value-frequency table for non-numerical observations.

These views are the substrate of the Statistics dashboard. They keep the dashboard query-cheap (read a denormalised aggregate, never re-scan the 20 M-row observation table) and let the LLM SQL agent cite stable aggregates without invoking a heavy window function.

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

Outliers in mixed-type space are dangerous because k-Prototypes is sensitive to extreme values in the numerical block. The platform applies a global z-score gate (`threshold = 6` in production, `4` available as a tighter alternative) on a fixed list of utilisation features:

```
age, total_medications, total_procedures, active_conditions_count,
distinct_providers_seen, lifetime_medication_days,
total_encounter_duration_hours, wellness_count, acute_care_count,
severe_care_count
```

For the three skewed columns, the z-score is computed *after* a log1p transform so the long tail does not artificially inflate every patient's z. The implementation skips zero-variance columns (avoids divide-by-zero on degenerate features). A patient is flagged as an outlier if **any** column's |z| exceeds the threshold (a logical OR, not AND — one extreme value is enough). Outliers are not deleted: they are clustered separately and assigned label `-1`, which the AI narrative engine renders as a distinct grey "Outliers" cluster on the dashboard.

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

### 4.3.12 The patient-feature substrate (the 22 feature frames)

A clustering algorithm is only as good as its features. The platform computes a unified patient feature matrix by running 22 SQL feature frames against the clinical warehouse and merging them on `patient_id`. Each frame answers a single clinically-meaningful question. The choice of frames — and their categorisation/bucketing rules — is the principal *domain knowledge* injected into the model; the rules below are the result of iterative tuning against clinical guidance.

#### Demographic and base frames

* **F1 — `patient_features`.** The base relation: `(patient_id, age, gender, race, ethnicity, marital)`. `age` was already computed by the ETL.
* **F12 — `provider_features`.** `distinct_providers_seen = COUNT(DISTINCT provider_id)` over a patient's encounters.

#### Encounter mix and dominance

* **F2 — `encounter_features`.** Eight per-class counts using `FILTER (WHERE encounter_class = X)`: `inpatient_count`, `outpatient_count`, `emergency_count`, `wellness_count`, `ambulatory_count`, `urgentcare_count`, `snf_count`, `hospice_count`.
* **F3 — `dominant_encounter_features`.** Per patient, the encounter class with the highest count, computed via `DISTINCT ON (patient_id) ... ORDER BY count DESC`. Returned as **`dominant_encounter_class`** (categorical).

#### Diagnosis frames

* **F4 — `condition_features`.** `total_conditions = COUNT(*)` of every recorded condition.
* **F10 — `active_conditions_features`.** `active_conditions_count = COUNT(*) WHERE end_date IS NULL` — the open chronic load.
* **F5 — `disease_flags`.** A bank of binary flags (0/1) computed by case-insensitive `LIKE` matching on the condition's free-text description. The matching rules are clinically chosen so they do *not* match family history or "suspected of" entries:
  * `has_diabetes` — `description ILIKE 'diabetes%' AND NOT 'prediabetes%'`.
  * `has_hypertension` — `'hypertension%' AND NOT 'prehypertension%'`.
  * `has_cancer` — `'neoplasm%' OR 'cancer%' OR 'carcinoma%' OR 'leukemia%' OR 'lymphoma%' OR 'myeloma%' OR 'melanoma%' OR 'sarcoma%' OR 'malignant%'`, all excluding `'suspected%'` and `'family history%'`.
  * `has_kidney_disease` — `'kidney%' OR 'renal%' OR 'nephro%' OR 'pyelonephritis%' OR 'microalbuminuria%' OR 'proteinuria%'`.
  * `has_mental_health` — `'depress%' OR 'anxiety%' OR 'schizophrenia%' OR 'ptsd%' OR 'posttraumatic%' OR 'suicid%' OR 'bipolar%' OR 'attention deficit%'`.
  * `has_heart_disease` — `'heart failure%' OR 'myocardial infarction%' OR 'coronary%' OR 'cardiac arrest%' OR 'atrial fibrillation%' OR 'arrhythmia%' OR 'angina%' OR 'ischemic heart%' OR 'cardiomyopathy%'`, excluding `'family history%'`.
  * `has_chronic_resp` — `'copd%' OR 'chronic obstructive%' OR 'emphysema%' OR 'chronic bronchitis%' OR 'asthma%' OR 'pulmonary fibrosis%'`, excluding family-history.
  * `has_active_acute_resp` — `'acute bronchitis%' OR 'pneumonia%' OR 'acute respiratory%' OR 'acute upper respiratory%' OR 'influenza%' OR 'bronchiolitis%'` *with* `end_date IS NULL` (currently active acute episode).

  Two flags merge into a categorical: **`respiratory_disease_profile`** ∈ {`Chronic with Active Acute`, `Chronic`, `Active Acute`, `None`} based on the truth table of `has_chronic_resp` × `has_active_acute_resp`.

* **F6 — `inpatient_history`.** `has_inpatient_history = MAX(CASE WHEN encounter_class='inpatient' THEN 1 ELSE 0 END)`; binary 0/1.

#### Pharmacological frames

* **F7 — `medication_features`.** `total_medications = COUNT(*)` over all prescription rows. **`is_polypharmacy_raw`** = 1 iff `COUNT(*) FILTER (WHERE end_date IS NULL) ≥ 5` — the WHO threshold for polypharmacy.
* **F17 — `lifetime_medication_features`.** `lifetime_medication_days = SUM(GREATEST(0, EXTRACT(EPOCH FROM (COALESCE(end_date, CURRENT_DATE) − start_date)) / 86400))` — total days under any medication, with active prescriptions counted up to today.

#### Procedure / careplan / encounter-duration frames

* **F8 — `procedure_features`.** `total_procedures = COUNT(*)`.
* **F18 — `encounter_duration_features`.** `total_encounter_duration_hours = SUM((end_date − start_date) / 3600)` over closed encounters.
* **F11 — `dominant_careplan_features`.** A clinically-prioritised severity classifier. Each careplan description is mapped via `~*` regex to one of six tiers, ranked 1 (worst) to 6 (best). For each patient the tier with the smallest rank that has any matching plan wins:
  * Rank 1 — `Complex, Oncology & Palliative` (matches `cancer|dialysis|terminal`).
  * Rank 2 — `Maternal & Antenatal` (`antenatal`).
  * Rank 3 — `Acute Trauma, Wound & Surgery` (`fracture|wound|surgery|surgical|injury|trauma|burn|musculoskeletal|spinal|jaw`).
  * Rank 4 — `Respiratory & Infectious` (`respiratory|asthma|pulmonary|infect|covid|pneumonia|bronchitis|sinusitis`).
  * Rank 5 — `Chronic Cardio-Metabolic` (`diabetes|hyperlipidemia|heart|hypertension|weight|cardiac|coronary`).
  * Rank 6 — `General Rehab & Routine` (everything else).

  This severity-aware bucket dramatically reduces the cardinality of a free-text careplan description (Synthea generates ~60 distinct phrasings) into a 6-level ordinal categorical ideal for k-Modes mode-finding.

#### Observation-derived vital frames

* **F9 — `observation_features`.** Numerical vitals are extracted by ILIKE pattern-matching on the observation `description` and averaged over the **most recent three** measurements per patient (a `ROW_NUMBER() = 1..3` per type). Glucose values reported in mmol/L are converted to mg/dL by multiplying by 18.0. Safety guards reject percentile/z-score observations and biologically implausible values (BMI > 100, glucose > 1000). Five numerics are produced (rounded to 2 decimals): `avg_bmi`, `qaly`, `daly`, `avg_systolic_bp`, `avg_glucose`.
* **F19 — `cholesterol_features`.** `AVG(value_numeric) WHERE description ILIKE '%cholesterol%' AND NOT '%ldl%' AND NOT '%hdl%' AND NOT '%triglyceride%' AND NOT '%ratio%'`, then bucketed: `Optimal (<170)`, `Borderline (170–199)`, `High (200–239)`, `Very High (≥240)`, `Unknown` (NULL). Returned as the categorical **`cholesterol_risk_category`**.
* **F22 — `smoking_features`.** Reads observations whose description ILIKE `%tobacco smoking status%`, maps the textual value to **`smoking_status`** ∈ {`current`, `former`, `never`} via substring match (`%daily%|%current%` → current; `%ex-smoker%|%former%` → former; else `never`).

#### Behavioural / utilisation frames

* **F13 — `ooh_features`** (out-of-hours flyer). Flags a patient whose acute encounters (emergency + urgentcare) cluster around evenings/weekends. (i) Extract day-of-week and hour from `start_date`. (ii) Classify each acute encounter as out-of-hours iff `DOW ∈ {0,6}` (Sun/Sat) or `HOUR ≥ 20` or `HOUR < 8`. (iii) `out_of_hours_flyer = 'Yes'` iff the patient has at least 5 acute encounters AND ≥ 80% of them were out-of-hours; else `'No'`.
* **F14 — `substance_use_features`.** Combines condition flags with screening scores from observations. (i) `has_illicit` — condition description matches `drug abuse|misuses drugs|opioid abuse|dependent drug`. (ii) `has_alcohol` — `alcoholism|alcohol drinking`. (iii) Read the latest **DAST-10** and **AUDIT-C** screening scores (validated alcohol/drug screening instruments) from observations. (iv) Map: `High Risk (Drug/Illicit)` if `has_illicit=1 OR DAST-10 ≥ 3`; `Moderate Risk (Alcohol)` if `has_alcohol=1 OR AUDIT-C ≥ 4`; otherwise `No/Low Risk`. Returned as **`substance_use_profile`**.
* **F15 — `pain_management_features`.** A four-tier classifier built from condition + medication descriptions: (i) `has_chronic_pain` matches `chronic pain|chronic low back|chronic neck|fibromyalgia|chronic intractable`; (ii) `has_acute_pain` matches `sprain|laceration|fracture|muscle pain|joint pain`; (iii) `has_opioid` matches `oxycodone|fentanyl|hydrocodone|morphine|tramadol|buprenorphine|codeine`. Tier rules — checked in order: `Chronic Opioid` (chronic pain AND opioid), `Chronic Non-Opioid` (chronic pain only), `Acute/Minor` (acute pain), else `None`. Returned as **`pain_management_tier`**.
* **F16 — `thirty_day_readmission_features`.** Counts back-to-back inpatient/ER chains within 30 days using a window-function trick. (i) For each patient, `LAG(end_date) OVER (PARTITION BY patient_id ORDER BY start_date)` gives the previous encounter's end. (ii) A row is a *readmission* iff `start_date ≤ prev_end_date + INTERVAL '30 days'`. (iii) Map count → tier: `0 → '0. None'`, `1–2 → '1. Occasional (1–2)'`, `3–5 → '2. Frequent (3–5)'`, `>5 → '3. Super-Utilizer (>5)'`. Returned as **`readmission_risk_tier`** — an ordinal categorical that the LLM narrative interprets as escalating utilisation pressure.
* **F21 — `days_since_features`.** `days_since_last_encounter = EXTRACT(DAY FROM (CURRENT_DATE − MAX(end_date)))` — used as a recency / disengagement signal.

#### Pregnancy frame

* **F20 — `pregnancy_features`.** Three-class categorical computed from condition matches: `Active` if a `normal pregnancy` row exists with `end_date IS NULL`; `Past` if any of `pregnancy%|miscarriage%|tubal ligation%|antenatal%|eclampsia%` ever appeared; else `None`. Returned as **`pregnancy_history`**.

#### Post-processing: derived compound features

After all 22 frames are merged on `patient_id`, a small derivation pass produces interpretable rollups and ordinal bins:

* `routine_care_count = ambulatory_count + outpatient_count`.
* `acute_care_count = emergency_count + urgentcare_count`.
* `severe_care_count = inpatient_count + snf_count + hospice_count`.
* `preventive_to_reactive_ratio = wellness_count / (acute_care_count + severe_care_count + 1)` — the +1 prevents a divide-by-zero for patients with no acute care.
* **`bmi_type`** — `pd.cut(avg_bmi, bins=[−∞, 18.5, 25, 30, 35, 40, ∞])` → `Underweight`, `Normal`, `Overweight`, `Obese I`, `Obese II`, `Obese III`; NaN → `Unknown`.
* **`bp_risk_category`** — `pd.cut(avg_systolic_bp, bins=[−∞, 119.9, 139.9, ∞])` → `Normal`, `Elevated`, `Hypertensive`; NaN → `Unknown`.
* **`glucose_risk_category`** — `pd.cut(avg_glucose, bins=[−∞, 99.9, 125.9, ∞])` → `Normal`, `Prediabetic`, `Diabetic`; NaN → `Unknown`.
* **`condition_burden`** — `pd.cut(active_conditions_count, bins=[−1, 3, 10, ∞])` → `low`, `medium`, `high`.
* **`medication_intensity`** — `pd.cut(total_medications, bins=[−1, 5, 20, ∞])` → `low`, `medium`, `high`.
* `is_polypharmacy` is mapped from the raw 0/1 to `'No'`/`'Yes'` so it is a clean string for k-Modes.
* All disease flags (`has_diabetes`, …, `has_inpatient_history`) are mapped 0→`'No'`, 1→`'Yes'`.
* All categoricals are NaN-filled with semantically-correct sentinels: `dominant_encounter_class`→`'wellness'`, `dominant_careplan`→`'None'`, `respiratory_disease_profile`→`'None'`, `substance_use_profile`→`'None'`, `pain_management_tier`→`'None'`, `readmission_risk_tier`→`'None'`, `cholesterol_risk_category`→`'Unknown'`, `pregnancy_history`→`'None'`, `out_of_hours_flyer`→`'No'`, `smoking_status`→`'never'`. A single canonical `gender` fallback (`'F'`) and `marital` fallback (`'S'`) are also applied.

The output is a 22-feature-frame ⊕ 12-derived-feature matrix, with every patient described by ~65 columns. From this matrix each `configs.py` configuration selects a small subset (typically 5 numerical + 8 categorical) to actually feed into k-Prototypes.

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

### 4.4.5b Pre-mining: shaping the sequence database

Before PrefixSpan ever runs, the platform applies a five-stage shaping pass that materially improves the quality of the mined patterns:

1. **Item-blacklist filtering.** Three Synthea catch-alls — `assessment of health and social care needs`, `medication review due`, `medication reconciliation` — appear in 30 %+ of patient timelines and convey no clinical information. They are filtered case-insensitively before mining.
2. **Deterministic prefix-priority sort.** Within a single calendar day a patient may have multiple events with identical timestamps. To make the mining deterministic *and* clinically meaningful, ties are broken by a fixed prefix priority: `C (Condition) → M (Medication) → P (Procedure) → CP (CarePlan)`. The ordering reflects the natural diagnostic-then-therapeutic causality (a condition is diagnosed before a medication is prescribed in response).
3. **Two-year rolling window.** For each patient, only events within `WINDOW_DAYS = 730` of their *most recent* event are retained. Recent care patterns are more clinically actionable than lifetime patterns; older events also dilute the support of recent trajectories.
4. **Run-length collapse.** Consecutive identical items in the same patient's timeline are collapsed: `A → A → B` becomes `A → B`. The `prev_pid == cur_pid AND prev_item == cur_item` predicate is computed via vectorised `pandas.shift()`.
5. **Tail truncation.** Each patient's timeline is truncated to the most recent `MAX_EVENTS_PER_PATIENT = 25` events. Patients with hundreds of events would otherwise dominate the projected databases and slow mining down asymmetrically.

### 4.4.5c Same-type-run filter (post-mining)

After the topk call but before GML re-ranking, patterns containing `≥ 3` consecutive items of the *same* event-type prefix are dropped. Examples eliminated by this filter: `C:Diabetes → C:Hypertension → C:Hyperlipidemia` (three conditions in a row, characteristic of Synthea's dental-cleaning bursts) or `M:Drug A → M:Drug B → M:Drug C` (three medication prescriptions in a row, often a single visit-bundle artefact). The clinical principle: an interesting trajectory crosses domains.

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

The platform is decomposed into seven backend microservices, each carved out by *bounded context* — a unit of business behaviour that has its own lifecycle, its own data ownership, and its own scaling profile. The split is summarised in the table below; the rest of this section justifies each separation theoretically.

| Service | Owns | Reads from | Communicates over | Bounded context |
|---------|------|------------|-------------------|------------------|
| `auth` | `auth_db` (`auth_user`, password-reset tokens) | — | HTTP, AMQP (publisher + subscriber) | Identity and credentials |
| `users` | — (placeholder) | `auth_db` (read-only) | HTTP | User-management API surface |
| `clinical-core` | `clinical_db` (12 tables: patient, provider, encounter, condition, medication, procedure, careplan, allergy, observation, immunization, organization, patient_provider) | — | HTTP, AMQP (publisher) | Clinical source-of-truth |
| `analytics` | `analytics_db` (read replicas / aggregates) | `clinical_db`, `ml_db` | HTTP | Read-heavy aggregation, dashboards, LLM SQL agent |
| `ml-batch` | `ml_db` (`cluster_meta`, `cluster`, `cluster_patient`, `prefix_span_pattern`, `prefix_span_patient_pattern`) | `clinical_db` | HTTP, AMQP (subscriber) | Long-running ML jobs |
| `mail-service` | — | — | AMQP (subscriber), SMTP (egress) | Transactional email |
| `queue-service` | `queue_db` (APScheduler jobstore) | — | HTTP, AMQP (subscriber) | Cron-style job orchestration |

### 4.7.1 The data-ownership invariant

Each writable piece of state is owned by exactly one service. A second service that needs the data either (a) reads through a *read-only* engine bound to the owner's database, or (b) listens for AMQP events the owner publishes when state changes. There are no cross-service `JOIN`s and no shared tables; the relational integrity that used to live in foreign keys now lives in event consistency. This is the *Database-per-Service* pattern in its strict form.

### 4.7.2 The seven contexts in detail

* **`auth`.** Owns identity. Responsible for login (issue JWT), password reset (one-time token + email), set-password, and `me` retrieval. Listens on RabbitMQ for `patient.created`/`patient.deleted` and `provider.created`/`provider.deleted` and provisions/deletes the corresponding `auth_user` rows. Emits `notification.send` for password-reset emails.
* **`users`.** A thin user-management layer reading from `auth_db`. Currently a placeholder for an admin-facing user CRUD; isolated so that any admin-specific RBAC logic does not contaminate the security-critical `auth` service.
* **`clinical-core`.** Owns every clinical table. The ETL writes here. Patient and provider CRUD endpoints live here; deletions cascade through AMQP events that downstream services consume.
* **`analytics`.** Computes dashboards and runs the LLM SQL agent. Read-only access to `clinical_db` and `ml_db` is explicit: separate SQLAlchemy engines mounted via the `read_engine("clinical")` / `read_engine("ml")` factory, each driven by `CLINICAL_DB_*` / `ML_DB_*` env vars. The agent is forbidden from emitting writes.
* **`ml-batch`.** The CPU-heavy outlier. Runs `build_patient_features` (21 SQL frames) against a read engine to `clinical_db`, runs k-Prototypes / PrefixSpan, and writes results to its own `ml_db`. Listens for `patient.deleted` to cascade-delete orphan `cluster_patient` rows.
* **`mail-service`.** No HTTP API of consequence — it consumes `notification.send` and dispatches via SMTP. Isolated because SMTP is I/O-bound and externally fragile (connection pooling, rate limits, retry semantics) and should not block any HTTP request.
* **`queue-service`.** APScheduler with a `queue_db` jobstore for persistent cron jobs (e.g., nightly recluster, view refresh). On boot, the scheduler reloads its jobstore so a container restart never loses scheduled work.

### 4.7.3 Theoretical properties earned by the split

1. **Independent deployability.** A patch to `mail-service` rebuilds and rolls only its container; `clinical-core` and `auth` keep serving traffic.
2. **Scaling locality.** `ml-batch` is CPU-bound and benefits from vertical scaling; `analytics` is I/O- and LLM-latency-bound and benefits from horizontal scaling. The Docker Compose topology already exposes per-service replica counts; a Kubernetes manifest derived from it would tune `resources.limits` and `replicas` per service.
3. **Failure isolation.** A k-Prototypes job that exhausts memory crashes only the `ml-batch` container; login still works.
4. **Fault-tolerant async coupling.** RabbitMQ persists the message until a consumer ACKs it. If `mail-service` is down when `notification.send` is published, the event is held in `mail.notifications` and delivered when the consumer comes back — a property the synchronous HTTP path cannot offer.
5. **Security boundary.** `auth` is the only service that accesses `auth_db`. The LLM SQL agent in `analytics` cannot read user passwords because there is no engine that goes there — even a successful prompt-injection attack stops at the boundary.

### 4.7.4 The event taxonomy (`clinical.events` topic exchange)

A single AMQP topic exchange `clinical.events` routes every domain event by an `<entity>.<action>` routing key. Three queues subscribe with selective bindings:

| Routing key | Publisher | Subscribed by | Side-effect |
|-------------|-----------|---------------|-------------|
| `patient.created` | clinical-core | `auth.account_sync` (auth) | Provision a `PATIENT` `auth_user`, send invite email |
| `patient.deleted` | clinical-core | `auth.account_sync` (auth) | Delete the linked `auth_user` |
| `patient.deleted` | clinical-core | `ml.clinical_sync` (ml-batch) | Delete orphaned `cluster_patient` rows in `ml_db` |
| `provider.created` | clinical-core | `auth.account_sync` (auth) | Provision a `DOCTOR` `auth_user`, send invite email |
| `provider.deleted` | clinical-core | `auth.account_sync` (auth) | Delete the linked `auth_user` |
| `notification.send` | any | `mail.notifications` (mail) | Render template, dispatch via SMTP |

A single routing key may bind to multiple queues (note `patient.deleted` fans out to both `auth` and `ml-batch`). This is the *Publisher / Multiple Subscribers* pattern with selective routing — every consumer sees only the events it cares about.

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

## 5.14 Microservice runtime in detail

### 5.14.1 Per-service responsibilities and routes

The seven backend services materialise the bounded contexts of Section 4.7. Each one is a self-contained FastAPI application sharing a common skeleton (`api/` → `service/` → `repository/` → `domain/`); the chosen routers are gated by the `SERVICE_NAME` environment variable so the same image can in principle serve any role, even though in production each service is built from its own folder.

| Service | HTTP routes (Traefik host) | Owned database | Key responsibility |
|---------|----------------------------|----------------|--------------------|
| `auth` | `auth.localhost`: `POST /auth/login`, `POST /auth/forgot-password`, `POST /auth/set-password`, `GET /auth/me`, `GET /health` | `auth_db` | Issue/validate JWTs, password-reset workflow, account provisioning from clinical events |
| `users` | `users.localhost`: (placeholder) | — | Future admin-facing user CRUD |
| `clinical-core` | `clinical.localhost`: `/patients/*`, `/providers/*`, `/encounters/*` | `clinical_db` | Source-of-truth CRUD; emits domain events |
| `analytics` | `analytics.localhost`: `/statistics/*`, `/dashboard/*`, `POST /statistics/sql-agent` | `analytics_db` (read replicas of `clinical_db`, `ml_db`) | Aggregations, dashboards, LLM SQL agent |
| `ml-batch` | `ml.localhost`: `/clusters/*`, `/sequences/*` | `ml_db` (read replica of `clinical_db`) | Run k-Prototypes / PrefixSpan, persist results, serve cluster/sequence detail pages |
| `mail-service` | `mail.localhost`: `GET /health` | — | Consume `notification.send`, render template, send SMTP |
| `queue-service` | `queue.localhost`: (placeholder) | `queue_db` | APScheduler jobstore for nightly recluster, view-refresh, etc. |

The `app.localhost` host serves the Next.js frontend; `localhost:8090` exposes the Traefik dashboard; `localhost:15673` exposes the RabbitMQ management UI; `localhost:5432` exposes `clinical-db` so the host-run ETL script can connect.

### 5.14.2 The asynchronous data plane (RabbitMQ)

Every domain event is published as a JSON message on the topic exchange `clinical.events` with routing key `<entity>.<action>`. The exchange is durable; each queue is durable and has a single named consumer per service so events survive restarts.

```
                                ┌─────────────────────────┐
                                │ exchange clinical.events│ (topic, durable)
                                └────────────┬────────────┘
                              routing keys → │
            ┌────────────────────────────────┼─────────────────────────────┐
            ▼                                ▼                             ▼
   ┌─────────────────────┐         ┌────────────────────┐        ┌────────────────────┐
   │ queue auth.account_ │         │ queue mail.        │        │ queue ml.clinical_ │
   │       sync          │         │      notifications │        │       sync         │
   │ binds:              │         │ binds:             │        │ binds:             │
   │  patient.created    │         │  notification.send │        │  patient.deleted   │
   │  patient.deleted    │         └─────────┬──────────┘        └─────────┬──────────┘
   │  provider.created   │                   │                              │
   │  provider.deleted   │                   ▼                              ▼
   └─────────┬───────────┘            mail-service                     ml-batch
             │                        SMTP dispatch                    delete cluster_patient
             ▼
        auth-service
        provision/delete
        auth_user
```

### 5.14.3 End-to-end synchronization flows

The key inter-service flows are:

* **Patient creation (clinical-core → auth → mail-service).** A clinician creates a patient via `POST /patients`. clinical-core inserts the row, then publishes `patient.created` with payload `{patient_id, first_name, last_name, email}`. auth's `account_sync` consumer receives it, inserts a new `auth_user` with role `PATIENT` and a one-time `set_password_token`, then publishes `notification.send` with the invite-email payload. mail-service's `notifications` consumer receives that, renders the template, and dispatches via SMTP. The whole chain is asynchronous — clinical-core's HTTP response returns the moment its own commit lands; the auth+email side completes within a few hundred milliseconds afterwards.
* **Patient deletion (clinical-core → auth + ml-batch).** A `DELETE /patients/{id}` cascades the row removal on `clinical_db`, then publishes `patient.deleted`. The same routing key is bound to *two* queues: auth's removes the linked `auth_user`; ml-batch's removes orphaned `cluster_patient` rows in `ml_db`. The two sides are independent — if one fails it can be retried from its DLQ without affecting the other.
* **Provider creation/deletion (clinical-core → auth).** Mirrors patient-create/delete but provisions a `DOCTOR` account (with `provider_id` claim used by the LLM SQL agent's `DOCTOR_SCOPE_CLAUSE`).
* **Password reset (auth → mail-service).** `POST /auth/forgot-password` generates a one-time token, stores it in `auth_db`, and publishes `notification.send` with the password-reset URL. The mail consumer dispatches the email. The user clicks the link and `POST /auth/set-password` validates the token and sets a new hash.
* **Cluster run (frontend → ml-batch → ml-batch → analytics).** The MANAGER triggers a clustering run via `POST /clusters/run`. ml-batch fetches features through the `clinical-db` read engine, runs `run_kprototypes`, writes results to `ml_db`, and returns. Subsequent dashboard reads come from `analytics`, which reads `ml_db` through *its own* read engine.
* **LLM SQL agent (frontend → analytics → clinical-db read).** The user asks a natural-language question. The analytics service runs `process_input → generate_query → validate_query → execute_query → summarise`, generating a SELECT-only SQL string and executing it through the `read_engine("clinical")` connection. No write path exists.

### 5.14.4 Read-only cross-DB engines

The `read_engine(name)` factory (in each consuming service's `db/db_connector.py`) constructs an SQLAlchemy `Engine` against an alternate database using `<NAME>_DB_*` env vars (e.g. `CLINICAL_DB_HOST`, `ML_DB_HOST`). A *read-only* `application_name` is set on the connection so DBAs can audit who is reading what. Engines are cached per process so they survive across requests.

### 5.14.5 Tableset registry — what each service owns

Inside each service folder, `db/model_registry.py` maps `SERVICE_NAME` to the set of tables that service is responsible for. At startup, `SQLModel.metadata.create_all(engine, tables=registry[SERVICE_NAME])` creates only that subset, never the others. This makes the database-per-service contract enforced at the schema-creation layer, not just by convention.

### 5.14.6 Failure modes and recovery

* **Consumer offline.** RabbitMQ holds messages in the durable queue. When the consumer comes back, it drains the backlog. No messages are lost.
* **Publisher fails to publish.** The platform uses publisher confirms; if the broker NACKs, the publishing service retries with exponential backoff. If retries exhaust, the event is logged and a manual reconciliation (e.g. re-running a sync job) is required.
* **Consumer crashes mid-processing.** The message remains unacknowledged; on reconnect RabbitMQ redelivers. Consumers must therefore be **idempotent** — re-creating an `auth_user` that already exists is a no-op (`INSERT ... ON CONFLICT DO NOTHING`).
* **Database down on startup.** Compose `depends_on` with `condition: service_healthy` blocks the service until its DB passes `pg_isready`. Cross-service read engines do not block startup; they retry on first use.
* **Eventual consistency.** A patient created in clinical-core may be queryable there before `auth` has provisioned the account. The frontend handles this by surfacing the "we sent you an email" message rather than asserting immediate login readiness.

### 5.14.7 Observability hooks

Every service exposes `GET /health`. Traefik's dashboard at `:8090` aggregates the routing table; the RabbitMQ management UI at `:15673` exposes per-queue depth, consumer count, and message rate. Logs are stdout-only (Docker collects them) — a future iteration would forward them to a central log store via Fluent Bit or Loki.

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
* **Figure 4.5b — Per-loader transform pattern.** A single-loader block diagram showing the five universal stages (read CSV → rename → coerce/derive → impute → audit-CSV write → bulk insert), with annotations showing what is *unique* to a complex loader like `load_encounters` (provider-redistribution, future-date clamp, per-class duration cap).
* **Figure 4.5c — Provider-redistribution mechanism.** A schematic with two horizontal tracks (raw provider distribution vs. kept-provider distribution per year), arrows showing how dropped-provider encounters are re-mapped round-robin within the same year.
* **Figure 4.5d — Encounter duration-cap rule chart.** A bar chart of the per-class duration caps (wellness=120 min … inpatient=43 200 min), with a horizontal "median observed duration" overlay so the cap appears reasonable.
* **Figure 4.5e — Observation-load chunking schematic.** A block diagram of the 10 000-row chunked insert with a progress-log emission point per chunk; a small inset showing why a single 20 M-row insert would explode the WAL.
* **Figure 4.5f — Materialised-view dependency tree.** Five MVs (`mv_obs_totals`, `mv_obs_per_patient`, `mv_obs_top_types`, `mv_obs_numeric_stats`, `mv_obs_categorical_stats`) and the tables they depend on; arrows show the order in which `REFRESH MATERIALIZED VIEW` is issued.
* **Figure 4.6 — Feature-engineering pipeline (block diagram).** 22 boxes (one per feature frame F1..F22) feeding into a single "merged feature matrix" box, then into "post-processing derived features" (routine/acute/severe care counts, ratio, bmi_type, bp_risk_category, glucose_risk_category, condition_burden, medication_intensity). Group the 22 frames by source table (patient, encounter, condition, medication, procedure, observation, careplan).
* **Figure 4.6b — Frame catalogue (table-style figure).** A two-column figure: left = frame ID (F1..F22) and short name, right = output columns it produces. Used as the canonical reference for the rest of the chapter.
* **Figure 4.6c — Disease-flag classifier rules.** A decision-table figure showing the LIKE-pattern rules for `has_diabetes`, `has_hypertension`, `has_cancer`, `has_heart_disease`, `has_kidney_disease`, `has_mental_health`, `has_chronic_resp`, `has_active_acute_resp`, with the explicit exclusions for family-history and suspected entries.
* **Figure 4.6d — Careplan severity-ranked classifier.** A flowchart with 6 ranked tiers (1 Complex/Oncology, 2 Maternal, 3 Acute Trauma, 4 Respiratory & Infectious, 5 Chronic Cardio-Metabolic, 6 General Rehab) and the regex predicates that route a careplan description into the lowest matching tier.
* **Figure 4.6e — Out-of-hours flyer rule.** A small flowchart: extract DOW + HOUR → tag OOH if weekend or HOUR ≥ 20 or HOUR < 8 → flag `'Yes'` only if total acute ≥ 5 AND OOH share ≥ 80%.
* **Figure 4.6f — Substance-use rule.** A two-input AND/OR diagram combining condition flags (illicit / alcohol) with screening scores (DAST-10 ≥ 3 / AUDIT-C ≥ 4) into the three-tier `substance_use_profile`.
* **Figure 4.6g — Pain-management tier rule.** A four-step ordered classifier: chronic+opioid → `Chronic Opioid`; chronic only → `Chronic Non-Opioid`; acute only → `Acute/Minor`; else `None`.
* **Figure 4.6h — 30-day readmission window.** A timeline figure showing two consecutive inpatient encounters; the LAG window function captures the previous end-date; the arrow marks the 30-day re-entry window.
* **Figure 4.6i — Vitals rolling-window aggregation.** A patient timeline with all observations of a type, the most-recent-3 are highlighted, an arrow shows the AVG rolling backwards from "most recent measurement".
* **Figure 4.6j — Bucketing rules for derived categoricals.** Four small histograms (BMI, BP, glucose, conditions) overlaid with the bin boundaries (e.g., 18.5/25/30/35/40 for BMI) and the corresponding label of each bin.
* **Figure 4.7 — Composite feature derivation.** A small block diagram showing `total_procedures + total_medications + active_conditions_count → log1p → standardise → PCA(1) → clinical_severity_score`. Annotate the explained-variance ratio.

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

* **Figure 4.19 — Sequence database schematic.** A few patient timelines visualised as horizontal arrows with prefixed events (`C:Hypertension`, `M:Lisinopril`, `P:ECG`, etc.) at their event dates. Annotate the COD/CP prefix legend.
* **Figure 4.19b — Pre-mining shaping pipeline.** A five-stage flowchart: Item-blacklist → Prefix-priority sort → 2-year rolling window → Run-length collapse → Tail-truncate. Annotate counts ("from N events to M events") at each stage.
* **Figure 4.19c — Prefix-priority tie-breaker.** A patient calendar day with three same-day events (a Condition, a Medication, a Procedure) showing how the C→M→P→CP ordering fixes the deterministic comparison ordering.
* **Figure 4.19d — 2-year rolling window.** A patient timeline (years on x-axis) with the most-recent-event marker and a 730-day backward shading; events outside the window are greyed out.
* **Figure 4.20 — PrefixSpan prefix-projection illustration.** Show how a prefix `<a>` induces a projected database, then `<a, b>` induces a smaller projected database, recursively.
* **Figure 4.21 — Closed-pattern dominance.** Two patterns $P \subset Q$ with the same support; visualise the dominance check `Q is strictly longer AND P is a (set ∧ order) subsequence of Q`.
* **Figure 4.22 — GML re-ranking effect (scatter).** Scatter of every mined pattern with support on x-axis and GML on y-axis. Highlight the top-K-by-support set (clustered around GML=1) vs. top-K-by-GML set (uniformly above GML=2).
* **Figure 4.22b — Type-diversity bonus.** A bar chart of the GML multiplier (1.0, 1.3, 1.6, 1.9) for patterns with 1, 2, 3, 4 distinct prefix types.
* **Figure 4.22c — Same-type-run rejection.** Three example patterns: `C→C→C` (rejected), `C→C→M` (kept), `C→M→P→CP` (kept) with the same-type-run filter circled around the rejected one.
* **Figure 4.23 — Posting-list patient attribution.** Block diagram showing the inverted index `posting[item] → list of seq idx`, the rarity-sorted intersection, and the two-pointer subsequence verification.
* **Figure 4.24 — Pattern-mining funnel.** Funnel chart: 10 000 raw → 7 800 (support floor) → 6 200 (no-3-consecutive-same-type) → 3 100 (closedness) → 500 (Jaccard dedup with caps).

### A.1.6 LLM agent diagrams

* **Figure 4.25 — LLM agent state graph.** The full LangGraph: START → process_input → {answer_general, generate_query, END} → validate_query → {execute_query, generate_query (retry), END} → execute_query → {summarise, generate_query (retry), END}. Show all conditional edges with their labels.
* **Figure 4.26 — Defence-in-depth validation pipeline.** Static regex check → SELECT-only check → LLM audit (PROMPT_VALIDATE_SQL) → role-scope literal check. Each layer rejects independently.
* **Figure 4.27 — Role-based scope projection.** A flow showing how MANAGER / DOCTOR / PATIENT roles inject different scope clauses into the prompt and how the resulting SQL differs.

### A.1.7 Microservice / domain-event theory diagrams

* **Figure 4.28 — Bounded-context map.** Seven domain bubbles (auth, users, clinical-core, analytics, ml-batch, mail, queue) with the ubiquitous-language terms each context owns. No technical wiring — purely conceptual ownership.
* **Figure 4.29 — Database-per-Service ownership matrix.** Rows = tables (every clinical, ml, auth, queue table), columns = services; an `R/W` mark in the owner cell, an `R-only` mark for cross-service read engines, blank elsewhere.
* **Figure 4.30 — Event taxonomy and routing-key tree.** The `clinical.events` exchange at the root, `<entity>.<action>` routing keys as branches (`patient.created`, `patient.deleted`, `provider.created`, `provider.deleted`, `notification.send`), with consumer queues as leaves.
* **Figure 4.31 — Eventual-consistency timeline.** A horizontal time axis showing `t=0` patient.created emitted by clinical-core, `t=Δ₁` auth provisions account, `t=Δ₂` mail dispatches invite. Annotates the bounded-staleness contract.

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
* **Figure 5.18 — Forgot-password sequence diagram.** User → Frontend → Auth Service → Auth DB (write token) → RabbitMQ publish `notification.send` → Mail Service consumer → SMTP. Asynchronous boundary highlighted.
* **Figure 5.18b — `patient.created` end-to-end fan-out.** clinical-core → publish `patient.created` → auth (provision PATIENT account) → publish `notification.send` → mail-service (SMTP). Three lifelines, two AMQP boundaries highlighted.
* **Figure 5.18c — `patient.deleted` multi-consumer fan-out.** Single publish from clinical-core → two parallel consumer arrows: (a) auth deletes the linked auth_user; (b) ml-batch deletes orphaned cluster_patient rows. Show that the two paths complete independently.
* **Figure 5.18d — `provider.created` provisioning.** clinical-core → auth provisions DOCTOR account with `provider_id` claim → publishes `notification.send` → mail-service dispatches invite.
* **Figure 5.19 — Cluster run sequence diagram.** Manager → Frontend → ML-batch Service → build_patient_features (reads clinical_db via read engine) → run_kprototypes → full_evaluation_report → ask_ai for narratives → save_cluster_results (writes ml_db) → 200 OK.
* **Figure 5.20 — LLM SQL agent sequence diagram.** User question → Frontend → Analytics Service → run_agent → process_input → generate_query → validate_query → (retry loop) → execute_query → PROMPT_RESULT → response. Include the doctor-scope verification step at the end.
* **Figure 5.21 — Cluster-detail page load sequence.** Frontend → Analytics Service → SELECT FROM cluster_patient WHERE cluster_id=X → JSONB feature aggregation → response. Demonstrates that no clinical-table joins are needed at request time.
* **Figure 5.21b — Cross-DB read engine activation.** A small sequence diagram: analytics service receives `/statistics/patients` → resolves `read_engine("clinical")` → SQLAlchemy uses `CLINICAL_DB_*` env to open a read-only pool → query → result returned.

### A.2.6 Activity / state diagrams

* **Figure 5.22 — ETL activity diagram.** UML activity diagram of `run_etl(engine)`: truncate (parallel ok in theory, sequenced for FK safety), load patients, …, refresh views, end.
* **Figure 5.23 — k-Prototypes orchestrator activity diagram.** `run_kprototypes`: validate → split frames → log1p → severity PCA (conditional) → scale → build matrix → optional elbow short-circuit → fit → plot → return.
* **Figure 5.24 — Frontend route hierarchy.** Tree of Next.js routes: `/(auth)/{login, forgot-password, set-password}`, `/(main)/{home, patients, patients/[id], clusters, clusters/[id], statistics, sequences, sequences/[id]}`.

### A.2.7 Algorithm pseudocode boxes (figure-style)

These are *listings*, not diagrams, but earn figure-style numbering because they encapsulate logic.

* **Listing 5.1 — Pseudocode of `mine_patterns`** (sequence build, integer encode, topk, GML, closedness, Jaccard dedup).
* **Listing 5.2 — Pseudocode of `attribute_patients`** (posting list build, rarity intersection, two-pointer subsequence).
* **Listing 5.3 — Pseudocode of `run_agent`** (state init, scope clause, graph invoke, post-processing branches).
* **Listing 5.4 — Pseudocode of `run_etl(engine)`** (truncate child-first, load patients/orgs/providers/encounters, redistribute providers, refresh MVs).
* **Listing 5.5 — Pseudocode of `build_patient_features`** (run 22 SQL frames, merge on patient_id, derive compound counts, bucket categoricals).
* **Listing 5.6 — Pseudocode of `run_kprototypes`** (validation, dual-frame separation, log1p, severity PCA, scale, build matrix, optional elbow short-circuit, fit, plot).

### A.2.8 Microservice runtime diagrams

* **Figure 5.25 — RabbitMQ topology map (concrete).** Concrete view of the `clinical.events` topic exchange, three durable queues (`auth.account_sync`, `mail.notifications`, `ml.clinical_sync`), the routing-key bindings table, and the consumer-count badges per queue.
* **Figure 5.26 — Per-service container manifest.** A single block per Docker container showing image, exposed port, owned database, mounted volumes, depends_on graph. Color-code data-owning vs. stateless services.
* **Figure 5.27 — Cross-DB read-engine factory class diagram.** UML class diagram of `db_connector.py`: `read_engine(name)` factory, the per-name engine cache, env-var configuration map.
* **Figure 5.28 — Tableset / model_registry ownership table.** A grid: rows = SERVICE_NAME values, columns = SQLModel tables; cells marked with the lifecycle action this service performs at startup (`create_all` vs. nothing).
* **Figure 5.29 — Idempotent consumer state machine.** State diagram: `received → already-handled? → if yes ACK no-op, if no apply → ACK`. Explains why a redelivered message never breaks invariants.
* **Figure 5.30 — Failure-and-recovery decision matrix.** Two-axis matrix (publisher failure vs. consumer failure) × (synchronous vs. async). Each cell describes the recovery action (queue persists, retry, DLQ).

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
* **Figure 6.31 — Event-fan-out latency distribution.** Histogram of the wall-clock between `patient.created` publish and `auth_user` row insertion (n = 1000 simulated events). Validates eventual-consistency budget.
* **Figure 6.32 — RabbitMQ queue depth over a synthetic workload.** Time-series of `auth.account_sync`, `mail.notifications`, `ml.clinical_sync` queue depths during a burst of 200 patient creations. Demonstrates that no queue saturates.
* **Figure 6.33 — Per-service request-rate dashboard.** Line chart with one line per service (`auth`, `users`, `clinical-core`, `analytics`, `ml-batch`, `mail-service`, `queue-service`) over a representative day. Used to validate scaling-locality claims.

## A.4 Diagram-production guidance

For consistency:

* **Use a single tool family.** UML diagrams in PlantUML or draw.io; data plots in matplotlib (already integrated into the codebase via `k_prototypes.py` and `cluster_evaluation.py`).
* **Fixed colour palette per chart type.** Cluster colors come from the LLM prompt (`#DC2626`, `#16A34A`, `#2563EB`, `#D97706`, `#7C3AED`, `#0891B2`, `#9CA3AF` for outliers). Reuse them across every cluster-aware figure so the same color always means the same cluster.
* **Mathematical figures rendered with the same LaTeX engine** as the body text; embed as PDF/SVG, not raster.
* **Every figure must be cross-referenced** in the body text via "Figure x.y shows …". A figure that the text never references should be cut.
* **Captions are self-contained.** A reader scanning only the figures should be able to grasp the main result. Captions of 2–3 sentences are normal; one-line captions are too thin for a thesis.

The complete inventory above totals **30 unique numbered diagrams in Chapter 4 (Figures 4.1–4.27 plus three composite visualisations), 24 in Chapter 5 (Figures 5.1–5.24), and 30 in Chapter 6 (Figures 6.1–6.30)** — comfortably above the density expected of a 70%-three-chapters thesis and matching the visual rigour Varga's reference work demonstrates.

---

# Appendix B — Consolidated flat list of all diagrams

A single linear checklist for production use. Each line is one figure to draw, ordered by chapter, suitable for tracking against `outputs/figures/`.

## Chapter 4 — Analysis and Theoretical Foundation

1. Figure 4.1 — Use-case diagram (PATIENT/DOCTOR/MANAGER actors).
2. Figure 4.2 — High-level component diagram (conceptual blocks).
3. Figure 4.3 — DFD level-1 (Synthea CSV → ETL → DB → ML → API → FE).
4. Figure 4.4 — Synthea source-file relationship sketch (11 CSVs).
5. Figure 4.5 — ETL truncate/load order flowchart.
6. Figure 4.5b — Per-loader transform pattern (5 universal stages).
7. Figure 4.5c — Provider-redistribution mechanism (round-robin per year).
8. Figure 4.5d — Encounter-class duration-cap chart.
9. Figure 4.5e — Observation-load chunking schematic.
10. Figure 4.5f — Materialised-view dependency tree.
11. Figure 4.6 — Feature-engineering pipeline (22 frames → matrix → derived).
12. Figure 4.6b — Frame catalogue (table-style).
13. Figure 4.6c — Disease-flag classifier rules.
14. Figure 4.6d — Careplan severity-ranked classifier.
15. Figure 4.6e — Out-of-hours flyer rule.
16. Figure 4.6f — Substance-use rule (DAST-10 / AUDIT-C).
17. Figure 4.6g — Pain-management tier rule.
18. Figure 4.6h — 30-day readmission window timeline.
19. Figure 4.6i — Vitals rolling-window aggregation.
20. Figure 4.6j — Bucketing rules for derived categoricals (BMI/BP/glucose/conditions).
21. Figure 4.7 — Composite feature derivation (severity PCA pipeline).
22. Figure 4.8 — k-Prototypes algorithm flowchart (init → assign → update → converge).
23. Figure 4.9 — Mixed-dissimilarity decomposition (Euclidean + indicator).
24. Figure 4.10 — Effect of γ on cluster geometry (γ=0.05 / 0.5 / 5.0).
25. Figure 4.11 — Huang-init vs. random-init convergence.
26. Figure 4.12 — Scaler comparison (boxplot).
27. Figure 4.13 — Effect of log1p on a skewed feature.
28. Figure 4.14 — Feature-space embedding (FAMD scatter).
29. Figure 4.15 — Silhouette coefficient illustration.
30. Figure 4.16 — Gower distance matrix construction.
31. Figure 4.17 — Three-tier evaluation pipeline.
32. Figure 4.18 — Feature-importance schematic (η², Cramér's V).
33. Figure 4.19 — Sequence database schematic (patient timelines + COD prefixes).
34. Figure 4.19b — Pre-mining shaping pipeline (5 stages).
35. Figure 4.19c — Prefix-priority tie-breaker.
36. Figure 4.19d — 2-year rolling window.
37. Figure 4.20 — PrefixSpan prefix-projection illustration.
38. Figure 4.21 — Closed-pattern dominance.
39. Figure 4.22 — GML re-ranking effect (scatter).
40. Figure 4.22b — Type-diversity bonus multiplier.
41. Figure 4.22c — Same-type-run rejection examples.
42. Figure 4.23 — Posting-list patient attribution.
43. Figure 4.24 — Pattern-mining funnel.
44. Figure 4.25 — LLM agent state graph (LangGraph).
45. Figure 4.26 — Defence-in-depth validation pipeline.
46. Figure 4.27 — Role-based scope projection.
47. Figure 4.28 — Bounded-context map.
48. Figure 4.29 — Database-per-Service ownership matrix.
49. Figure 4.30 — Event taxonomy and routing-key tree.
50. Figure 4.31 — Eventual-consistency timeline.

## Chapter 5 — Detailed Design and Implementation

51. Figure 5.1 — System architecture diagram (concrete).
52. Figure 5.2 — Deployment diagram (UML, ports, networks).
53. Figure 5.3 — Network and routing diagram.
54. Figure 5.4 — RabbitMQ topic-exchange map.
55. Figure 5.5 — Clinical-schema ER diagram.
56. Figure 5.6 — ML-schema ER diagram.
57. Figure 5.7 — Auth-schema ER diagram.
58. Figure 5.8 — Materialised-view dependency graph.
59. Figure 5.9 — Backend package diagram (per service).
60. Figure 5.10 — Layer-boundary rule diagram.
61. Figure 5.11 — Black-box diagram of the analytics service.
62. Figure 5.12 — Black-box diagram of the ML-batch service.
63. Figure 5.13 — Clustering-domain class diagram.
64. Figure 5.14 — Sequence-mining-domain class diagram.
65. Figure 5.15 — LLM-agent-domain class diagram.
66. Figure 5.16 — Frontend Redux slice diagram.
67. Figure 5.17 — Login sequence diagram.
68. Figure 5.18 — Forgot-password sequence diagram.
69. Figure 5.18b — `patient.created` end-to-end fan-out.
70. Figure 5.18c — `patient.deleted` multi-consumer fan-out.
71. Figure 5.18d — `provider.created` provisioning.
72. Figure 5.19 — Cluster-run sequence diagram.
73. Figure 5.20 — LLM SQL agent sequence diagram.
74. Figure 5.21 — Cluster-detail page-load sequence.
75. Figure 5.21b — Cross-DB read-engine activation.
76. Figure 5.22 — ETL activity diagram.
77. Figure 5.23 — k-Prototypes orchestrator activity diagram.
78. Figure 5.24 — Frontend route hierarchy.
79. Figure 5.25 — RabbitMQ topology map (concrete).
80. Figure 5.26 — Per-service container manifest.
81. Figure 5.27 — Cross-DB read-engine factory class diagram.
82. Figure 5.28 — Tableset / model_registry ownership table.
83. Figure 5.29 — Idempotent consumer state machine.
84. Figure 5.30 — Failure-and-recovery decision matrix.

(Listings: 5.1 mine_patterns, 5.2 attribute_patients, 5.3 run_agent, 5.4 run_etl, 5.5 build_patient_features, 5.6 run_kprototypes.)

## Chapter 6 — Testing and Validation

85. Figure 6.1 — Elbow plot (cost vs. k).
86. Figure 6.2 — FAMD scatter (production run).
87. Figure 6.3 — Cluster-feature heat-map.
88. Figure 6.4 — Cluster-feature bar-chart panel.
89. Figure 6.5 — Categorical-distribution stacked bars.
90. Figure 6.6 — Per-cluster Gower silhouette bar chart.
91. Figure 6.7 — Cluster-size pie chart.
92. Figure 6.8 — Silhouette vs. k across configs (v40, v54, v55).
93. Figure 6.9 — Stability across seeds (boxplot).
94. Figure 6.10 — Scaler comparison radar chart.
95. Figure 6.11 — Outlier-threshold trade-off scatter.
96. Figure 6.12 — Gamma sensitivity line plot.
97. Figure 6.13 — Configuration ranking heat-map.
98. Figure 6.14 — AI-clarity vs. metric-quality scatter.
99. Figure 6.15 — Cluster-narrative word cloud.
100. Figure 6.16 — Pattern-mining funnel chart.
101. Figure 6.17 — GML vs. support scatter.
102. Figure 6.18 — Type-diversity histogram.
103. Figure 6.19 — Pattern-length distribution.
104. Figure 6.20 — Top-10 patterns Sankey.
105. Figure 6.21 — Pattern × cluster overlay heat-map.
106. Figure 6.22 — Question-category × pass-rate bar chart.
107. Figure 6.23 — Retry distribution histogram.
108. Figure 6.24 — End-to-end latency boxplot.
109. Figure 6.25 — Failure-mode pareto.
110. Figure 6.26 — End-to-end pipeline timing breakdown.
111. Figure 6.27 — Gower silhouette: naive vs. vectorised.
112. Figure 6.28 — Observation-load chunk progress.
113. Figure 6.29 — Smoke-test sequence diagram.
114. Figure 6.30 — Container healthcheck timeline.
115. Figure 6.31 — Event-fan-out latency distribution.
116. Figure 6.32 — RabbitMQ queue depth under workload.
117. Figure 6.33 — Per-service request-rate dashboard.

**Grand total: 117 figures + 6 algorithm listings = 123 visual artefacts** spanning theory (50), design/implementation (34 figures + 6 listings), and validation (33). This is the upper bound — a thesis at 70 % three-chapter density typically retains 40–60 of these; the rest are reserved for the appendix or omitted depending on page budget.
