DB_SCHEMA = """
=== HOSPITAL ANALYTICS DATABASE SCHEMA ===

OVERVIEW:
- 16 tables total: 4 infrastructure (patient, organization, provider, encounter) + 7 clinical (observation, condition, medication, procedure, immunization, allergy, careplan) + 2 sequence-mining (prefix_span_pattern, prefix_span_patient_pattern) + 3 clustering (cluster_meta, cluster, cluster_patient). Observation also has five pre-aggregated mv_obs_* materialized views for fast stats.
- The central entity is Patient. Organizations and Providers form the infrastructure.
- Encounters link Patients to Providers and Organizations (many-to-one).
- All clinical events (allergy, condition, immunization, medication, observation, procedure, careplan) are linked to a Patient and usually to the specific Encounter where they were recorded.
- The 3 clustering tables (cluster_meta, cluster, cluster_patient) store the current K-Prototypes patient segmentation.
- The 2 sequence-mining tables (prefix_span_pattern, prefix_span_patient_pattern) store frequent care-trajectory patterns discovered by PrefixSpan.
- Only use clustering or sequence tables when the user explicitly asks about clusters, patient segments, care trajectories, or sequences.

--- TABLES ---

TABLE: patient
  - patient_id (str, PK) - UUID. Never treat as integer.
  - birthdate (date) - Date of birth.
  - deathdate (date, nullable) - Date of death. NULL means the patient is alive.
  - age (int) - Pre-computed age of the patient.
  - first_name (str), last_name (str) - Patient name.
  - marital (str) - Marital status. Values: 'M' (Married), 'S' (Single), 'D' (Divorced), 'W' (Widowed).
  - race (str) - lowercase, exactly as stored. Values: 'white', 'black', 'asian', 'native', 'hawaiian', 'other'. Never 'White'/'Black'/etc.
  - ethnicity (str) - lowercase, no space or hyphen, exactly as stored. Values: 'hispanic', 'nonhispanic'. Never 'Hispanic'/'Non-Hispanic'.
  - gender (str) - Values: 'M' (Male), 'F' (Female). Do NOT use 'Male'/'Female' in queries.
  - city (str) - City of residence.

TABLE: organization
  - organization_id (str, PK) - UUID.
  - name (str) - Hospital or clinic name (e.g. 'General Hospital').
  - city (str) - City location.
  - phone (str, nullable) - Contact phone number.
  - utilization (int) - Total number of patient encounters handled.

TABLE: provider
  - provider_id (str, PK) - UUID.
  - organization_id (str, FK → organization) - The organization the provider works at.
  - first_name (str), last_name (str) - Provider name.
  - gender (str, nullable) - Provider gender.
  - speciality (str) - Medical specialty (e.g. 'General Practice', 'Cardiology', 'Internal Medicine', 'Surgery').
  - city (str, nullable) - City location.
  - encounters (int) - Total number of encounters performed by this provider.
  - procedures (int) - Total number of procedures performed by this provider.

TABLE: encounter
  PURPOSE: Represents a patient visit/interaction with the healthcare system.
  - encounter_id (str, PK) - UUID.
  - patient_id (str, FK → patient).
  - organization_id (str, FK → organization).
  - provider_id (str, FK → provider).
  - start_date (datetime) - When the visit started.
  - end_date (datetime) - When the visit ended.
  - duration (float) - Length of visit in minutes.
  - encounter_class (str) - Type of visit. Values:
      'inpatient'   = hospital admission/hospitalization (internare)
      'ambulatory'  = outpatient clinic visit (consultatie ambulatorie)
      'outpatient'  = outpatient visit (similar to ambulatory)
      'wellness'    = routine checkup (control de rutina)
      'emergency'   = emergency room visit (urgenta)
      'urgentcare'  = urgent care visit
      'home'        = home visit
      'virtual'     = telemedicine/virtual visit
      'snf'         = skilled nursing facility
      'hospice'     = hospice/palliative care
  - description (str) - Reason for the visit (e.g. 'General examination of patient').
  - reason_description (str, nullable) - Additional clinical context.

TABLE: observation
  PURPOSE: Clinical measurements and lab results recorded during encounters.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter, nullable).
  - date (datetime) - Date of measurement.
  - observation_code (str) - LOINC code (e.g. '8310-5' = Body Temperature, '8480-6' = Systolic BP, '39156-5' = BMI, '2093-3' = Cholesterol).
  - description (str) - Human-readable name (e.g. 'Body Temperature', 'Hemoglobin A1c'). Use ILIKE for searching.
  - value (str) - Raw string value.
  - value_numeric (float, nullable) - Numeric result. Use for comparisons (e.g. value_numeric > 38).
  - units (str, nullable) - Unit of measurement (e.g. 'Cel', 'mm[Hg]', 'kg/m2', 'mg/dL').

TABLE: condition
  PURPOSE: Diagnosed medical conditions/diseases.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) - When the condition was diagnosed.
  - end_date (datetime, nullable) - When resolved. NULL = ongoing/chronic.
  - condition_code (str) - SNOMED-CT code.
  - description (str) - Condition name (e.g. 'Diabetes', 'Hypertension', 'Viral sinusitis', 'COVID-19'). Use ILIKE.

TABLE: medication
  PURPOSE: Prescribed medications/drugs.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) - When the medication was started.
  - end_date (datetime, nullable) - When stopped.
  - duration_days (float) - Pre-computed treatment length in days.
  - medication_code (str) - RxNorm code.
  - description (str) - Drug name (e.g. 'Amoxicillin', 'Lisinopril', 'Metformin'). Use ILIKE.
  - reason_description (str, nullable) - Why the medication was prescribed.

TABLE: procedure
  PURPOSE: Medical procedures performed on patients.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) - When the procedure was performed.
  - end_date (datetime, nullable) - When the procedure ended.
  - procedure_code (str) - SNOMED-CT code.
  - description (str) - Procedure name (e.g. 'Appendectomy', 'Colonoscopy', 'X-ray'). Use ILIKE.
  - reason_description (str, nullable) - Clinical reason for the procedure.

TABLE: immunization
  PURPOSE: Vaccinations administered to patients.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - date (datetime) - When the vaccine was given.
  - immunization_code (str) - CVX code (e.g. '140' = Influenza).
  - description (str) - Vaccine name (e.g. 'Influenza', 'COVID-19', 'Hepatitis B'). Use ILIKE.

TABLE: allergy
  PURPOSE: Patient allergies.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter, nullable).
  - start_date (date) - When the allergy was first recorded.
  - end_date (date, nullable) - When resolved. NULL = still active.
  - allergy_code (str) - SNOMED-CT code.
  - description (str) - Allergen name (e.g. 'Peanuts', 'Penicillin', 'Bee stings', 'Latex'). Use ILIKE.

TABLE: careplan
  PURPOSE: Longitudinal care plans assigned to patients (e.g. 'Diabetes self management plan', 'Cardiac care plan').
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) - When the care plan started.
  - end_date (datetime, nullable) - When concluded. NULL = still active.
  - duration_days (float, nullable) - Pre-computed plan length in days.
  - careplan_code (str) - SNOMED-CT code.
  - description (str) - Care plan name (e.g. 'Asthma self management', 'Self-care interventions'). Use ILIKE.
  - reason_code (str, nullable), reason_description (str, nullable) - Clinical reason for the plan.

TABLE: prefix_span_pattern
  PURPOSE: Frequent care-trajectory patterns discovered by PrefixSpan over patient event sequences.
           A "pattern" is an ordered sequence of clinical events; '->' denotes temporal order, items in parentheses occurred on the same day. Event prefixes: C: = Condition, M: = Medication, P: = Procedure, CP: = CarePlan.
  - id (int, PK, serial).
  - rank (int) - Ordering index for display; lower = higher-ranked in the mining output.
  - pattern_str (str) - Human-readable sequence (e.g. 'C:Hypertension -> M:Lisinopril'). Use ILIKE.
  - length (int) - Number of events in the sequence.
  - support_count (int) - How many distinct patients contain this pattern.
  - support_pct (float) - support_count / total patients, as a percentage.
  - cluster_label (int, nullable) - Which mining run produced this pattern: NULL = mined globally over the whole population; an integer (or -1 for the outlier group) = mined specifically for that cluster. For "how many/which patterns were mined for cluster X" filter this column directly - do NOT join through prefix_span_patient_pattern/cluster_patient for that question, since that instead finds patterns (from any run) that happen to have a member in cluster X.
  - ai_analysis (JSONB, nullable) - Cached AI-generated interpretation (not related_work for SQL queries).

TABLE: prefix_span_patient_pattern
  PURPOSE: Junction table - which patients contain which mined sequence.
  - pattern_id (int, PK, FK → prefix_span_pattern.id).
  - patient_id (str, PK, FK → patient).
  USAGE: JOIN to find patients who follow a pattern, or to count pattern frequency within a cluster.

TABLE: cluster_meta
  PURPOSE: Singleton - exactly one row storing the metadata for the current clustering run.
           Fully replaced (DELETE + INSERT) every time k_prototypes is re-executed.
  - id (int, PK, serial).
  - created_at (timestamp) - When the clustering was executed.
  - algorithm (str) - Always 'k_prototypes' currently.
  - n_clusters (int) - Number of clusters requested (e.g. 4).
  - n_patients (int) - Number of non-outlier patients that were clustered.
  - n_outliers (int) - Number of patients excluded as statistical outliers.
  - numerical_features (JSONB) - List of numerical feature names used (e.g. ["age", "qaly", "total_medications"]).
  - categorical_features (JSONB) - List of categorical feature names used (e.g. ["gender", "has_diabetes"]).
  - params (JSONB) - Algorithm parameters: scaler, gamma, init method, random_state, outlier_threshold.
  - metrics (JSONB) - Quality scores: silhouette, gower_silhouette, calinski_harabasz, davies_bouldin.
  - heatmap (bytes, nullable) - PNG image of cluster heatmap (binary, not related_work for SQL queries).
  - pca_image (bytes, nullable) - PNG image of PCA/FAMD scatter plot (binary, not related_work for SQL queries).
  - ai_analysis (JSONB, nullable) - Cached AI-generated population analysis (not related_work for SQL queries).

TABLE: cluster
  PURPOSE: One row per cluster. Stores the AI-generated summary for each patient group.
           Fully replaced on every clustering run.
  - id (int, PK, serial).
  - cluster_label (int) - Cluster index: 0, 1, 2, ... or -1 for the outlier group.
  - color (str) - Hex color code for UI display (e.g. '#DC2626').
  - title (str) - Short AI-generated cluster name (e.g. 'Metabolic Strain').
  - description (str) - AI-generated clinical description of this patient group.
  - insight (str) - Key clinical finding for this cluster.
  - recommendation (str) - Suggested clinical action for this cluster.
  - ai_analysis (JSONB, nullable) - Cached detailed per-cluster AI analysis.

TABLE: cluster_patient
  PURPOSE: Maps each patient to their assigned cluster. One row per patient.
           Fully replaced on every clustering run.
  - id (int, PK, serial).
  - patient_id (str, FK → patient).
  - cluster_label (int) - Which cluster this patient belongs to (-1 = outlier).
  - is_outlier (bool) - TRUE if the patient was excluded as a statistical outlier.
  - pca_x (float, nullable) - X coordinate from PCA 2D projection (for scatter plot).
  - pca_y (float, nullable) - Y coordinate from PCA 2D projection (for scatter plot).
  - features (JSONB) - All engineered features for this patient at clustering time. Keys include:
      Numerical: age, qaly, total_medications, total_procedures, active_conditions_count,
                 routine_care_count, acute_care_count, wellness_count, severe_care_count,
                 clinical_severity_score, distinct_providers_seen.
      Categorical: gender, dominant_careplan, condition_burden, bmi_type.
      Historical runs may additionally persist: avg_bmi, avg_systolic_bp, avg_glucose, daly,
      days_since_last_encounter, marital, smoking_status, dominant_encounter_class,
      has_diabetes, has_hypertension, has_heart_disease, has_cancer, has_respiratory_disease,
      has_mental_health, is_polypharmacy. If a key is absent the value is NULL.
      Value notes:
        - Yes/No flags are stored as string 'Yes'/'No'.
        - smoking_status: 'never', 'former', 'current'.
        - condition_burden: 'low', 'medium', 'high' (binned from active_conditions_count).
        - dominant_careplan: 'Cardiac', 'Respiratory', 'Metabolic', 'Maternal', 'Musculoskeletal', 'Psychiatric', 'Other', 'none'.
  INDEXES: ix_cluster_patient_patient_id on (patient_id).
  USAGE: To query feature values use JSONB operators, e.g.: features->>'age', (features->>'age')::numeric.

--- KEY RELATIONSHIPS ---

patient (1) → (N) encounter → (1) organization
patient (1) → (N) encounter → (1) provider
encounter (1) → (N) observation, condition, medication, procedure, immunization, allergy, careplan
provider (N) → (1) organization
cluster_meta (1) - singleton run metadata
cluster (N) - one row per cluster label
patient (1) → (0..1) cluster_patient - current cluster assignment
prefix_span_pattern (1) → (N) prefix_span_patient_pattern → (1) patient

To find which hospital a patient visited: JOIN encounter ON patient_id, then JOIN organization ON organization_id.
To find which doctor treated a patient: JOIN encounter ON patient_id, then JOIN provider ON provider_id.
To find which cluster a patient belongs to: JOIN cluster_patient ON patient_id.
To get all patients in a specific cluster: SELECT patient_id FROM cluster_patient WHERE cluster_label = <N> AND NOT is_outlier.
To find which patients follow a care-trajectory pattern: JOIN prefix_span_patient_pattern ON pattern_id.
To count how many patients in a cluster share a sequence: JOIN prefix_span_patient_pattern pp ON pp.patient_id = cluster_patient.patient_id, then GROUP BY pp.pattern_id.

--- CLUSTERING SEMANTIC MAPPINGS ---

"cluster" / "segment" / "grup de pacienti" → cluster table (summaries) + cluster_patient (membership)
"outlier" / "exceptie" → cluster_patient WHERE is_outlier = TRUE (or cluster_label = -1)
"which cluster is patient X in" → SELECT cluster_label FROM cluster_patient WHERE patient_id = 'X'
"patients in cluster N" → SELECT patient_id FROM cluster_patient WHERE cluster_label = N AND NOT is_outlier
"cluster quality" / "calitatea clusteringului" → SELECT metrics FROM cluster_meta LIMIT 1
"feature value for patient" → SELECT features->>'<feature_name>' FROM cluster_patient WHERE patient_id = '...'

--- SEMANTIC MAPPINGS (multilingual) ---

These map common natural-language terms to the correct database concepts:

"hospitalization" / "internare" / "admission" → encounter WHERE encounter_class = 'inpatient'
"visit" / "vizita" / "consultatie" → encounter (any encounter_class, or 'ambulatory' if outpatient)
"emergency" / "urgenta" → encounter WHERE encounter_class = 'emergency'
"checkup" / "control" → encounter WHERE encounter_class = 'wellness'
"last" / "most recent" / "ultima" / "cel mai recent" → ORDER BY date DESC LIMIT 1
"first" / "earliest" / "prima" → ORDER BY date ASC LIMIT 1
"how many" / "cati" / "cate" / "numar" → COUNT(*)
"average" / "medie" → AVG()
"disease" / "boala" / "diagnostic" → condition table
"treatment" / "tratament" / "medicament" → medication table
"surgery" / "operatie" / "interventie" → procedure table
"vaccine" / "vaccin" → immunization table
"allergy" / "alergie" → allergy table
"care plan" / "plan de ingrijire" / "plan de tratament" → careplan table
"doctor" / "medic" → provider table
"hospital" / "spital" / "clinica" → organization table
"patient" / "pacient" → patient table
"sequence" / "trajectory" / "pattern" / "traseu" / "secventa" → prefix_span_pattern table (mining results) + prefix_span_patient_pattern (membership)
"blood pressure" / "tensiune" → observation WHERE description ILIKE '%blood pressure%'
"temperature" / "temperatura" → observation WHERE description ILIKE '%body temperature%'
"BMI" → observation WHERE observation_code = '39156-5'
"alive" / "in viata" → patient WHERE deathdate IS NULL
"deceased" / "decedat" → patient WHERE deathdate IS NOT NULL

--- EXAMPLE QUERIES ---

Q: "When was the last hospitalization?"
SQL: SELECT start_date FROM encounter WHERE encounter_class = 'inpatient' ORDER BY start_date DESC LIMIT 1;

Q: "How many patients have diabetes?"
SQL: SELECT COUNT(DISTINCT patient_id) FROM condition WHERE description ILIKE '%diabetes%';

Q: "Which hospital handled the most emergencies?"
SQL: SELECT o.name, COUNT(*) AS total FROM encounter e JOIN organization o ON e.organization_id = o.organization_id WHERE e.encounter_class = 'emergency' GROUP BY o.name ORDER BY total DESC LIMIT 1;

Q: "What is the average age of female patients?"
SQL: SELECT AVG(age) AS average_age FROM patient WHERE gender = 'F';

Q: "List all medications prescribed for hypertension."
SQL: SELECT DISTINCT m.description FROM medication m WHERE m.reason_description ILIKE '%hypertension%' ORDER BY m.description LIMIT 100;

Q: "How many patients are in each cluster?"
SQL: SELECT c.cluster_label, c.title, COUNT(cp.patient_id) AS patient_count FROM cluster c JOIN cluster_patient cp ON c.cluster_label = cp.cluster_label WHERE NOT cp.is_outlier GROUP BY c.cluster_label, c.title ORDER BY c.cluster_label;

Q: "What is the average age of patients in cluster 0?"
SQL: SELECT ROUND(AVG((features->>'age')::numeric), 1) AS avg_age FROM cluster_patient WHERE cluster_label = 0 AND NOT is_outlier;

Q: "Which cluster does patient with id '...' belong to?"
SQL: SELECT cp.cluster_label, c.title FROM cluster_patient cp JOIN cluster c ON cp.cluster_label = c.cluster_label WHERE cp.patient_id = '...';

Q: "What are the diabetes rates per cluster?"
SQL: SELECT cluster_label, ROUND(100.0 * SUM(CASE WHEN features->>'has_diabetes' = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS diabetes_pct FROM cluster_patient WHERE NOT is_outlier GROUP BY cluster_label ORDER BY cluster_label;

Q: "Which cluster is dominated by the cardiac careplan?"
SQL: SELECT cluster_label, COUNT(*) AS patients FROM cluster_patient WHERE NOT is_outlier AND features->>'dominant_careplan' = 'Cardiac' GROUP BY cluster_label ORDER BY patients DESC LIMIT 1;

Q: "Average systolic blood pressure per cluster?"
SQL: SELECT cluster_label, ROUND(AVG((features->>'avg_systolic_bp')::numeric), 1) AS avg_sbp FROM cluster_patient WHERE NOT is_outlier GROUP BY cluster_label ORDER BY cluster_label;

Q: "What is the clustering quality score?"
SQL: SELECT metrics->>'silhouette' AS silhouette, metrics->>'davies_bouldin' AS davies_bouldin, metrics->>'calinski_harabasz' AS calinski_harabasz FROM cluster_meta LIMIT 1;

Q: "How many patients have an active care plan for diabetes?"
SQL: SELECT COUNT(DISTINCT patient_id) AS total FROM careplan WHERE description ILIKE '%diabetes%' AND end_date IS NULL;

Q: "Which care plans are most common?"
SQL: SELECT description, COUNT(*) AS total FROM careplan GROUP BY description ORDER BY total DESC LIMIT 10;

Q: "What are the top 5 most frequent care trajectories?"
SQL: SELECT rank, pattern_str, support_count, support_pct FROM prefix_span_pattern ORDER BY support_count DESC LIMIT 5;

Q: "Which sequences are most common in cluster 0?"
SQL: SELECT p.pattern_str, COUNT(DISTINCT pp.patient_id) AS cluster_support FROM prefix_span_patient_pattern pp JOIN cluster_patient cp ON pp.patient_id = cp.patient_id JOIN prefix_span_pattern p ON pp.pattern_id = p.id WHERE cp.cluster_label = 0 AND NOT cp.is_outlier GROUP BY p.id, p.pattern_str ORDER BY cluster_support DESC LIMIT 5;

Q: "How many sequence patterns were mined specifically for cluster 0?"
SQL: SELECT COUNT(*) AS total FROM prefix_span_pattern WHERE cluster_label = 0;
-- (direct column filter, NOT a join - this counts mining-run patterns, not pattern popularity among cluster-0 patients)

Q: "How many patients follow any care trajectory containing hypertension?"
SQL: SELECT COUNT(DISTINCT pp.patient_id) AS total FROM prefix_span_patient_pattern pp JOIN prefix_span_pattern p ON pp.pattern_id = p.id WHERE p.pattern_str ILIKE '%hypertension%';
"""
