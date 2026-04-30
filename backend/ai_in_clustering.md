# AI in Clustering

This document explains how AI is used to interpret patient clusters after k-prototypes constructs them, and how the `/clusters/ai-analysis/{cluster_id}` endpoint works.

---

## 1. Cluster summarization during the clustering run

After `run_kprototypes()` finishes, `get_clusters_summary()` (in `k_prototypes.py`) is called. It builds a single prompt for all clusters at once and calls `ask_ai(prompt)`. The result is stored in the database via `save_cluster_results()`.

### What data is sent to the AI

For each cluster (including cluster `-1` for outliers), the prompt contains:

**Key averages (numerical means across all patients in the cluster):**

| Field | Meaning |
|---|---|
| `age` | Mean patient age in years |
| `qaly` | Quality-Adjusted Life Year — 1.0 = perfect health, 0 = death |
| `daly` | Disability-Adjusted Life Years — years of healthy life lost; higher = more disease burden |
| `total_procedures` | Total number of medical procedures across the patient's history |
| `total_medications` | Total distinct medications ever prescribed |
| `active_conditions_count` | Number of currently open (unresolved) conditions |
| `lifetime_medication_days` | Cumulative days of medication coverage across all prescriptions (active meds counted to today) |
| `total_encounter_duration_hours` | Sum of all encounter durations in hours |

> `clinical_severity_score` is intentionally excluded from the LLM prompt — it is a standardized PCA z-score and not interpretable in absolute terms. The raw inputs (`total_procedures`, `total_medications`, `active_conditions_count`) are used instead.

**Demographics and disease rates (categorical summaries):**

| Field | Meaning |
|---|---|
| `dominant_gender` | Statistical mode of `gender` within the cluster (`M`/`F`) |
| `dominant_marital` | Mode of marital status (`M`, `S`, `D`, `W`) |
| `main_encounter_type` | Mode of `dominant_encounter_class` (ambulatory, wellness, emergency, etc.) |
| `dominant_careplan` | Mode of the clinical careplan category assigned to each patient |
| `diabetes_rate` | % of patients flagged `has_diabetes = Yes` |
| `hypertension_rate` | % of patients flagged `has_hypertension = Yes` |
| `heart_disease_rate` | % of patients flagged `has_heart_disease = Yes` |
| `cancer_rate` | % of patients flagged `has_cancer = Yes` |
| `polypharmacy_rate` | % of patients with 5+ concurrent active medications |
| `bmi_mix` | Proportion of each BMI category (Underweight / Normal / Overweight / Obese I-III / Unknown) |
| `bp_mix` | Proportion of blood pressure categories (Normal / Elevated / Hypertensive / Unknown) |
| `glucose_mix` | Proportion of glucose risk categories (Normal / Prediabetic / Diabetic / Unknown) |
| `substance_use_mix` | Proportion of substance use profiles (No/Low Risk / Moderate Risk (Alcohol) / High Risk (Drug/Illicit)) |
| `readmission_mix` | Proportion of 30-day readmission tiers (0. None / 1. Occasional / 2. Frequent / 3. Super-Utilizer) |

**Careplan mix:** top-4 dominant careplan categories by patient share (e.g. `{"Chronic Cardio-Metabolic": 0.62, ...}`).

**Top clinical entities (by frequency within the cluster):**
- Top 4 conditions
- Top 3 medications
- Top 3 procedures

### How the AI is forced to answer in the correct format

The prompt contains an explicit structure rule and a concrete example:

```
Structure your response EXACTLY as a list, using the pipe character (|) to separate the fields:
[Cluster ID] | [#HexColor] | [Short Title] | [1-2 sentences Description] | [1 short sentence Insight] | [1 short sentence Recommendation]
```

Additional rules injected into the prompt:

- **Title**: 2-4 words, plain everyday language, no medical jargon (e.g. "Older Adults with Chronic Conditions").
- **Description**: 1-2 short sentences understandable by a non-medical reader.
- **Insight**: The single most distinguishing signal for this cluster — must include a concrete number (e.g. disease rate, average medication count).
- **Recommendation**: One action tied directly to the insight.
- **Color**: A strong, vivid, fully-saturated hex color that reflects the clinical profile. The prompt provides guidance: red tones for high-risk, green for healthy, blue for elderly chronic, orange for moderate, purple for psychiatric, teal for maternal. Cluster `-1` (outliers) is always `#9CA3AF` (gray).
- Em dashes (`-`) are explicitly forbidden — the AI must use commas or plain sentence structure.

An example output line is included in the prompt so the AI has a concrete template to follow.

### How the response is parsed

`_parse_cluster_summaries()` in `save_results.py` processes the raw AI text line by line:

1. Each line is matched against the regex `\[(-?\d+)\]\s*\|(.+)` to extract the cluster ID and the rest.
2. The remainder is split on `|` into 5 parts: `color`, `title`, `description`, `insight`, `recommendation`.
3. Lines with fewer than 5 parts are discarded.
4. If the color field does not start with `#`, the fallback color `#006780` is used.
5. Duplicate cluster IDs are deduplicated (first occurrence wins).

The parsed rows are inserted into the `cluster` table.

---

## 2. The `/clusters/ai-analysis/{cluster_id}` endpoint

**Route:** `GET /clusters/ai-analysis/{cluster_id}`  
**Auth:** Requires manager role (`require_manager(scope)` — doctors cannot access this endpoint).  
**Response model:** `AiAnalysisResponse`

### What the endpoint does

This endpoint produces a **deep per-cluster analysis** — richer and more clinically detailed than the summary generated during the clustering run. Results are cached in the `cluster.ai_analysis` JSONB column so the LLM is only called once per cluster per run.

**Execution flow:**

1. **Fast path (cache hit):** `repo.get_cluster_ai_analysis(cluster_id)` reads `cluster.ai_analysis`. If it is not null, return immediately — no LLM call.
2. **Slow path — row lock:** `repo.lock_cluster_ai_analysis(cluster_id)` acquires a `SELECT ... FOR UPDATE` lock on the cluster row and rechecks the cache. This prevents multiple concurrent requests from all triggering a separate LLM call.
3. **Context assembly:** `repo.get_ai_context(cluster_id)` fetches all statistics from the database (see below).
4. **Prompt construction:** `ClusterService._build_prompt(ctx)` fills `PROMPT_AI_ANALYSIS` (defined in `cluster_service.py`) with the fetched statistics.
5. **LLM call:** `ask_ai(prompt)` sends the filled prompt to GPT (`gpt-5.4` via the OpenAI client in `llm_models.py`, 60 s timeout, 2 retries).
6. **Parsing:** `parse_ai_json(raw)` strips any markdown code fences (` ```json ``` `) and calls `json.loads()`.
7. **Cache write:** `repo.save_cluster_ai_analysis(cluster_id, analysis)` persists the parsed dict to `cluster.ai_analysis` and commits.
8. **Return:** `AiAnalysisResponse(**analysis)`.

### Parameters fed into the prompt

**Clustering quality metrics** (from `cluster_meta.metrics`):

| Parameter | Meaning |
|---|---|
| `silhouette` | Silhouette score — ranges -1 to 1; values near 1 mean well-separated, cohesive clusters |
| `davies_bouldin` | Davies-Bouldin index — lower is better; measures within-cluster scatter vs between-cluster separation |

These two metrics are shown so the AI can calibrate how confident to be about cluster boundaries.

**Population baseline** (computed across all non-outlier patients — used as comparison deltas):

| Parameter | Meaning |
|---|---|
| `pop_avg_age` | Population mean age |
| `pop_avg_bmi` | Population mean BMI |
| `pop_avg_systolic_bp` | Population mean systolic blood pressure (mmHg) |
| `pop_avg_glucose` | Population mean blood glucose (mg/dL) |
| `pop_avg_qaly` | Population mean QALY |
| `pop_avg_daly` | Population mean DALY |
| `pop_avg_meds` | Population mean total medications |
| `pop_avg_procedures` | Population mean total procedures |
| `pop_avg_conditions` | Population mean active conditions |
| `pop_avg_days_since` | Population mean days since last encounter |
| `pop_diabetes_pct` | Population-wide diabetes prevalence % |
| `pop_hypertension_pct` | Population-wide hypertension prevalence % |
| `pop_heart_pct` | Population-wide heart disease prevalence % |
| `pop_cancer_pct` | Population-wide cancer prevalence % |
| `pop_polypharmacy_pct` | Population-wide polypharmacy prevalence % |

**Cluster-specific statistics:**

| Parameter | Source | Meaning |
|---|---|---|
| `title`, `description` | `cluster` table | Pre-assigned by the clustering summary step |
| `cluster_type` | derived | `"outlier group"` if id == -1, else `"regular cluster"` |
| `count`, `pct` | `cluster_patient` | Patient count and % of all patients |
| `avg_age` | `patient.age` | Mean age in years |
| `avg_bmi` | `observation` (BMI ILIKE) | Mean BMI; <18.5 underweight, 18.5-25 normal, 25-30 overweight, ≥30 obese |
| `avg_systolic_bp` | `observation` (systolic BP ILIKE) | Mean systolic BP in mmHg; ≥140 = hypertensive range |
| `avg_glucose` | `observation` (glucose ILIKE, non-urine) | Mean blood glucose in mg/dL; ≥126 = diabetic, 100-125 = prediabetic |
| `avg_qaly` | `observation` (QALY ILIKE) | Mean Quality-Adjusted Life Year |
| `avg_daly` | `observation` (DALY ILIKE) | Mean Disability-Adjusted Life Years |
| `avg_conditions` | `condition` (end_date IS NULL) | Mean active (open) conditions per patient |
| `avg_meds` | `medication` | Mean total medications per patient |
| `avg_procedures` | `procedure` | Mean total procedures per patient |
| `avg_days_since` | `encounter.end_date` | Mean days since last completed encounter — proxy for care recency / follow-up gaps |
| `dominant_encounter_class` | `encounter` (mode) | Most frequent encounter type across the cluster |
| `dominant_careplan` | `cluster_patient.features` JSONB (mode) | Most common dominant careplan category |
| `dominant_marital` | `patient.marital` (mode) | Most common marital status |
| `female_pct`, `male_pct` | `cluster_patient.features["gender"]` | Gender split percentages |
| `diabetes_pct` | `condition` (LIKE patterns) | % with diabetes diagnosis |
| `hypertension_pct` | `condition` (LIKE patterns) | % with hypertension diagnosis |
| `heart_disease_pct` | `condition` (LIKE patterns) | % with heart failure / coronary / myocardial / AFib |
| `cancer_pct` | `condition` (LIKE patterns) | % with cancer / carcinoma / leukemia / lymphoma / malignant |
| `polypharmacy_pct` | `medication` (active count ≥ 5) | % with 5+ concurrent active medications |
| `current_smoker_pct`, `former_smoker_pct`, `never_smoker_pct` | `observation` (tobacco smoking status) | Smoking status breakdown |

### How the AI is forced to output the correct format

The prompt ends with an explicit JSON schema and the instruction:

```
Respond ONLY with valid JSON (no markdown, no extra text):
{
  "risk_level": "high or moderate or low",
  "medical_interpretation": "...",
  "layperson_summary": "...",
  "key_characteristics": [...],
  "priority_interventions": [...],
  "care_recommendations": [...]
}
```

Rules injected into the prompt:
- Every claim must be grounded in the provided numbers — no inferred traits.
- Gender: "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Comparisons must use the "vs population avg" deltas explicitly provided.
- Vitals must be translated to plain risk language (systolic ≥140 = hypertensive range, glucose ≥126 = diabetic range, BMI ≥30 = obese).
- The dominant careplan category must guide the clinical framing of the interpretation.
- Metrics that are `N/A` or 0 with no clinical meaning must be omitted.
- Em dashes are forbidden.

The `parse_ai_json()` helper strips markdown fences before parsing, so the AI output is robust to the model wrapping its JSON in ` ```json ``` `.

### Response fields

| Field | Type | Meaning |
|---|---|---|
| `risk_level` | `"high"` / `"moderate"` / `"low"` | Overall clinical risk assessment for the cluster |
| `medical_interpretation` | string | 2-3 sentences for clinicians: clinical definition, main risks, care gaps, with specific numbers and deltas |
| `layperson_summary` | string | 1-2 sentences for non-medical readers: plain language description of who these patients are |
| `key_characteristics` | list[string] | 4 data-grounded characteristics that define the cluster |
| `priority_interventions` | list[string] | 3 specific, actionable near-term clinical interventions |
| `care_recommendations` | list[string] | 3 longer-term system-level recommendations |

---

## 3. LLM model

Both the clustering summary step and the `/ai_analysis` endpoint use the same `ask_ai()` function in `service/lllm_sql_agent_service/llm_models.py`. It calls the OpenAI API with model `gpt-5.4`, a 60-second timeout, and 2 automatic retries for transient network errors.
