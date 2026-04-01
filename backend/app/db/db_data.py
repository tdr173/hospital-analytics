DB_SCHEMA = """
=== HOSPITAL ANALYTICS DATABASE SCHEMA ===

OVERVIEW:
- 13 tables total: 10 clinical tables + 3 clustering tables.
- The central entity is Patient. Organizations and Providers form the infrastructure.
- Encounters link Patients to Providers and Organizations (many-to-one).
- All clinical events (Allergy, Condition, Immunization, Medication, Observation, Procedure) are linked to a Patient and usually to the specific Encounter where they were recorded.
- The 3 clustering tables (cluster_run, cluster, cluster_patient) store results from K-Prototypes patient segmentation runs. Do NOT use these tables unless the user explicitly asks about clusters or patient segmentation.

--- TABLES ---

TABLE: patient
  - patient_id (str, PK) — UUID. Never treat as integer.
  - birthdate (date) — Date of birth.
  - deathdate (date, nullable) — Date of death. NULL means the patient is alive.
  - age (int) — Pre-computed age of the patient.
  - first_name (str), last_name (str) — Patient name.
  - marital (str) — Marital status. Values: 'M' (Married), 'S' (Single), 'D' (Divorced), 'W' (Widowed).
  - race (str) — Values: 'White', 'Black', 'Asian', 'Native', 'Other'.
  - ethnicity (str) — Values: 'Hispanic', 'Non-Hispanic'.
  - gender (str) — Values: 'M' (Male), 'F' (Female). Do NOT use 'Male'/'Female' in queries.
  - city (str) — City of residence.
  - latitude (float), longitude (float) — Geographic coordinates.

TABLE: organization
  - organization_id (str, PK) — UUID.
  - name (str) — Hospital or clinic name (e.g. 'General Hospital').
  - city (str) — City location.
  - latitude (float), longitude (float) — Geographic coordinates.
  - phone (str, nullable) — Contact phone number.
  - utilization (int) — Total number of patient encounters handled.

TABLE: provider
  - provider_id (str, PK) — UUID.
  - organization_id (str, FK → organization) — The organization the provider works at.
  - first_name (str), last_name (str) — Provider name.
  - gender (str, nullable) — Provider gender.
  - speciality (str) — Medical specialty (e.g. 'General Practice', 'Cardiology', 'Internal Medicine', 'Surgery').
  - city (str, nullable) — City location.
  - latitude (float), longitude (float) — Geographic coordinates.
  - utilization (int) — Number of encounters performed.

TABLE: encounter
  PURPOSE: Represents a patient visit/interaction with the healthcare system.
  - encounter_id (str, PK) — UUID.
  - patient_id (str, FK → patient).
  - organization_id (str, FK → organization).
  - provider_id (str, FK → provider).
  - start_date (datetime) — When the visit started.
  - end_date (datetime) — When the visit ended.
  - duration (float) — Length of visit in minutes.
  - encounter_class (str) — Type of visit. Values:
      'inpatient'   = hospital admission/hospitalization (internare)
      'ambulatory'  = outpatient clinic visit (consultatie ambulatorie)
      'wellness'    = routine checkup (control de rutina)
      'emergency'   = emergency room visit (urgenta)
      'urgentcare'  = urgent care visit
  - description (str) — Reason for the visit (e.g. 'General examination of patient').
  - reason_description (str, nullable) — Additional clinical context.

TABLE: observation
  PURPOSE: Clinical measurements and lab results recorded during encounters.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter, nullable).
  - date (datetime) — Date of measurement.
  - observation_code (str) — LOINC code (e.g. '8310-5' = Body Temperature, '8480-6' = Systolic BP, '39156-5' = BMI, '2093-3' = Cholesterol).
  - description (str) — Human-readable name (e.g. 'Body Temperature', 'Hemoglobin A1c'). Use ILIKE for searching.
  - value (str) — Raw string value.
  - value_numeric (float, nullable) — Numeric result. Use for comparisons (e.g. value_numeric > 38).
  - units (str, nullable) — Unit of measurement (e.g. 'Cel', 'mm[Hg]', 'kg/m2', 'mg/dL').

TABLE: condition
  PURPOSE: Diagnosed medical conditions/diseases.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) — When the condition was diagnosed.
  - end_date (datetime, nullable) — When resolved. NULL = ongoing/chronic.
  - condition_code (str) — SNOMED-CT code.
  - description (str) — Condition name (e.g. 'Diabetes', 'Hypertension', 'Viral sinusitis', 'COVID-19'). Use ILIKE.

TABLE: medication
  PURPOSE: Prescribed medications/drugs.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - start_date (datetime) — When the medication was started.
  - end_date (datetime, nullable) — When stopped.
  - duration_days (float) — Pre-computed treatment length in days.
  - medication_code (str) — RxNorm code.
  - description (str) — Drug name (e.g. 'Amoxicillin', 'Lisinopril', 'Metformin'). Use ILIKE.
  - reason_description (str, nullable) — Why the medication was prescribed.

TABLE: procedure
  PURPOSE: Medical procedures performed on patients.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - date (datetime) — When the procedure was performed.
  - procedure_code (str) — SNOMED-CT code.
  - description (str) — Procedure name (e.g. 'Appendectomy', 'Colonoscopy', 'X-ray'). Use ILIKE.
  - reason_description (str, nullable) — Clinical reason for the procedure.

TABLE: immunization
  PURPOSE: Vaccinations administered to patients.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter).
  - date (datetime) — When the vaccine was given.
  - immunization_code (str) — CVX code (e.g. '140' = Influenza).
  - description (str) — Vaccine name (e.g. 'Influenza', 'COVID-19', 'Hepatitis B'). Use ILIKE.

TABLE: allergy
  PURPOSE: Patient allergies.
  - id (int, PK).
  - patient_id (str, FK → patient).
  - encounter_id (str, FK → encounter, nullable).
  - start_date (date) — When the allergy was first recorded.
  - end_date (date, nullable) — When resolved. NULL = still active.
  - allergy_code (str) — SNOMED-CT code.
  - description (str) — Allergen name (e.g. 'Peanuts', 'Penicillin', 'Bee stings', 'Latex'). Use ILIKE.

TABLE: cluster_run
  PURPOSE: Metadata for a K-Prototypes patient clustering run. One row per execution.
  - id (int, PK, serial).
  - created_at (timestamp) — When the clustering was executed.
  - algorithm (str) — Always 'k_prototypes' currently.
  - n_clusters (int) — Number of clusters requested (e.g. 4).
  - n_patients (int) — Number of non-outlier patients that were clustered.
  - n_outliers (int) — Number of patients excluded as statistical outliers.
  - numerical_features (JSONB) — List of numerical feature names used (e.g. ["age", "qaly", "total_medications"]).
  - categorical_features (JSONB) — List of categorical feature names used (e.g. ["gender", "has_diabetes"]).
  - params (JSONB) — Algorithm parameters: scaler, gamma, init method, random_state, outlier_threshold.
  - metrics (JSONB) — Quality scores: silhouette, gower_silhouette, calinski_harabasz, davies_bouldin.
  - heatmap (bytes, nullable) — PNG image of cluster heatmap (binary, not useful for SQL queries).
  - ai_analysis (JSONB, nullable) — Cached AI-generated population analysis (not useful for SQL queries).
  NOTE: To get the most recent run use: SELECT MAX(id) FROM cluster_run.

TABLE: cluster
  PURPOSE: One row per cluster in a clustering run. Stores the AI-generated summary for each patient group.
  - id (int, PK, serial).
  - run_id (int, FK → cluster_run).
  - cluster_label (int) — Cluster index: 0, 1, 2, ... or -1 for the outlier group.
  - color (str) — Hex color code for UI display (e.g. '#DC2626').
  - title (str) — Short AI-generated cluster name (e.g. 'Metabolic Strain').
  - description (str) — AI-generated clinical description of this patient group.
  - insight (str) — Key clinical finding for this cluster.
  - recommendation (str) — Suggested clinical action for this cluster.
  - ai_analysis (JSONB, nullable) — Cached detailed per-cluster AI analysis.
  INDEXES: ix_cluster_run_id on (run_id).

TABLE: cluster_patient
  PURPOSE: Maps each patient to their assigned cluster for a given run. One row per patient per run.
  - id (int, PK, serial).
  - run_id (int, FK → cluster_run).
  - patient_id (str, FK → patient).
  - cluster_label (int) — Which cluster this patient belongs to (-1 = outlier).
  - is_outlier (bool) — TRUE if the patient was excluded as a statistical outlier.
  - pca_x (float, nullable) — X coordinate from PCA 2D projection (for scatter plot).
  - pca_y (float, nullable) — Y coordinate from PCA 2D projection (for scatter plot).
  - features (JSONB) — All engineered features for this patient at clustering time. Keys include:
      Numerical: age, qaly, total_procedures, total_medications, inpatient_count, outpatient_count,
                 emergency_count, wellness_count, ambulatory_count, urgentcare_count,
                 active_conditions_count, avg_bmi, days_since_last_encounter, total_immunizations.
      Categorical: gender, marital, dominant_encounter_class, has_diabetes, has_hypertension,
                   has_heart_disease, has_obesity, smoking_status, age_group, bmi_category,
                   condition_burden, medication_intensity.
  INDEXES: ix_cluster_patient_run_id on (run_id), ix_cluster_patient_patient_id on (patient_id).
  USAGE: To query feature values use JSONB operators, e.g.: features->>'age', (features->>'age')::numeric.

--- KEY RELATIONSHIPS ---

patient (1) → (N) encounter → (1) organization
patient (1) → (N) encounter → (1) provider
encounter (1) → (N) observation, condition, medication, procedure, immunization, allergy
provider (N) → (1) organization
cluster_run (1) → (N) cluster          [one run has multiple cluster summaries]
cluster_run (1) → (N) cluster_patient  [one run has one row per patient]
patient (1) → (N) cluster_patient      [a patient can appear in multiple runs]

To find which hospital a patient visited: JOIN encounter ON patient_id, then JOIN organization ON organization_id.
To find which doctor treated a patient: JOIN encounter ON patient_id, then JOIN provider ON provider_id.
To find which cluster a patient belongs to: JOIN cluster_patient ON patient_id WHERE run_id = (SELECT MAX(id) FROM cluster_run).
To get all patients in a specific cluster: SELECT patient_id FROM cluster_patient WHERE run_id = (SELECT MAX(id) FROM cluster_run) AND cluster_label = <N> AND NOT is_outlier.

--- CLUSTERING SEMANTIC MAPPINGS ---

"cluster" / "segment" / "grup de pacienti" → cluster table (summaries) + cluster_patient (membership)
"clustering run" / "rulare clustering" → cluster_run table
"outlier" / "exceptie" → cluster_patient WHERE is_outlier = TRUE (or cluster_label = -1)
"which cluster is patient X in" → SELECT cluster_label FROM cluster_patient WHERE patient_id = 'X' AND run_id = (SELECT MAX(id) FROM cluster_run)
"patients in cluster N" → SELECT patient_id FROM cluster_patient WHERE cluster_label = N AND run_id = (SELECT MAX(id) FROM cluster_run) AND NOT is_outlier
"cluster quality" / "calitatea clusteringului" → SELECT metrics FROM cluster_run WHERE id = (SELECT MAX(id) FROM cluster_run)
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
"doctor" / "medic" → provider table
"hospital" / "spital" / "clinica" → organization table
"patient" / "pacient" → patient table
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
SQL: SELECT c.cluster_label, c.title, COUNT(cp.patient_id) AS patient_count FROM cluster c JOIN cluster_patient cp ON c.run_id = cp.run_id AND c.cluster_label = cp.cluster_label WHERE c.run_id = (SELECT MAX(id) FROM cluster_run) AND NOT cp.is_outlier GROUP BY c.cluster_label, c.title ORDER BY c.cluster_label;

Q: "What is the average age of patients in cluster 0?"
SQL: SELECT ROUND(AVG((features->>'age')::numeric), 1) AS avg_age FROM cluster_patient WHERE run_id = (SELECT MAX(id) FROM cluster_run) AND cluster_label = 0 AND NOT is_outlier;

Q: "Which cluster does patient with id '...' belong to?"
SQL: SELECT cp.cluster_label, c.title FROM cluster_patient cp JOIN cluster c ON cp.run_id = c.run_id AND cp.cluster_label = c.cluster_label WHERE cp.patient_id = '...' AND cp.run_id = (SELECT MAX(id) FROM cluster_run);

Q: "What are the diabetes rates per cluster?"
SQL: SELECT cluster_label, ROUND(100.0 * SUM(CASE WHEN features->>'has_diabetes' = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS diabetes_pct FROM cluster_patient WHERE run_id = (SELECT MAX(id) FROM cluster_run) AND NOT is_outlier GROUP BY cluster_label ORDER BY cluster_label;

Q: "What is the clustering quality score?"
SQL: SELECT metrics->>'silhouette' AS silhouette, metrics->>'davies_bouldin' AS davies_bouldin, metrics->>'calinski_harabasz' AS calinski_harabasz FROM cluster_run WHERE id = (SELECT MAX(id) FROM cluster_run);
"""
