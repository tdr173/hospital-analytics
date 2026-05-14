import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.decomposition import PCA
from kmodes.kprototypes import KPrototypes
from dotenv import load_dotenv

from pathlib import Path

from sqlalchemy import text

from cluster_evaluation import full_evaluation_report, _fast_gower_matrix

from service.lllm_sql_agent_service import ask_ai
from save_results import save_cluster_results

current_folder = Path(__file__).parent

# Columns used for global z-score outlier detection. The three _SKEWED ones are
# log1p'd internally inside remove_outliers_zscore - z-scores on raw long-tailed
# counts flag too many "outliers" just for being on the tail.
OUTLIER_NUMERICAL_FEATURES = [
    "age",
    "total_medications",
    "total_procedures",
    "active_conditions_count",
    "distinct_providers_seen",
    "lifetime_medication_days",
    "total_encounter_duration_hours",
    "wellness_count",
    "acute_care_count",
    "severe_care_count",
]
_SKEWED_OUTLIER_COLS = {
    "total_medications",
    "lifetime_medication_days",
    "total_encounter_duration_hours",
}


def build_patient_features(engine) -> pd.DataFrame:
    patient_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   age,
                   gender,
                   race,
                   ethnicity,
                   marital
            FROM patient
            """
        ),
        con=engine,
    )

    encounter_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(*) FILTER (WHERE encounter_class = 'inpatient')   AS inpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'outpatient')  AS outpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'emergency')   AS emergency_count, COUNT(*) FILTER (WHERE encounter_class = 'wellness')    AS wellness_count, COUNT(*) FILTER (WHERE encounter_class = 'ambulatory')  AS ambulatory_count, COUNT(*) FILTER (WHERE encounter_class = 'urgentcare')  AS urgentcare_count, COUNT(*) FILTER (WHERE encounter_class = 'snf')         AS snf_count, COUNT(*) FILTER (WHERE encounter_class = 'hospice')     AS hospice_count
            FROM encounter
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    dominant_encounter_features = pd.read_sql(
        text(
            """
            SELECT DISTINCT
            ON (patient_id)
                patient_id,
                CASE
                WHEN encounter_class IN ('ambulatory','wellness','outpatient','emergency','urgentcare','inpatient')
                THEN encounter_class
                ELSE 'other'
            END
            AS dominant_encounter_class
                                                   FROM (
                                                       SELECT patient_id, encounter_class, COUNT(*) AS cnt
                                                       FROM encounter
                                                       GROUP BY patient_id, encounter_class
                                                   ) sub
                                                   ORDER BY patient_id, cnt DESC
            """
        ),
        con=engine,
    )

    condition_features = pd.read_sql(
        text("SELECT patient_id, COUNT(*) AS total_conditions FROM condition GROUP BY patient_id"),
        con=engine,
    )

    disease_flags = pd.read_sql(
        text(
            """
            WITH agg_conditions AS (SELECT patient_id,
                                           -- DIABETES - 12%
                                           MAX(CASE
                                                   WHEN (LOWER(description) LIKE '%%diabetes%%' OR
                                                         LOWER(description) LIKE '%%diabetic%%')
                                                       AND LOWER(description) NOT LIKE '%%prediabetes%%' THEN 1
                                                   ELSE 0 END) AS has_diabetes,

                                           -- HYPERTENSION - 20%
                                           MAX(CASE
                                                   WHEN LOWER(description) LIKE '%%hypertension%%'
                                                       AND LOWER(description) NOT LIKE '%%prehypertension%%' THEN 1
                                                   ELSE 0 END) AS has_hypertension,

                                           -- CANCER - 4.77%
                                           MAX(CASE
                                                   WHEN (LOWER(description) LIKE '%%neoplasm%%' OR
                                                         LOWER(description) LIKE '%%cancer%%'
                                                       OR LOWER(description) LIKE '%%carcinoma%%' OR
                                                         LOWER(description) LIKE '%%leukemia%%'
                                                       OR LOWER(description) LIKE '%%lymphoma%%' OR
                                                         LOWER(description) LIKE '%%myeloma%%'
                                                       OR LOWER(description) LIKE '%%melanoma%%' OR
                                                         LOWER(description) LIKE '%%sarcoma%%'
                                                       OR LOWER(description) LIKE '%%malignant%%')
                                                       AND LOWER(description) NOT LIKE '%%suspected%%'
                                                       AND LOWER(description) NOT LIKE '%%family history%%' THEN 1
                                                   ELSE 0 END) AS has_cancer,

                                           -- KIDNEY DISEASE - 8%
                                           MAX(CASE
                                                   WHEN LOWER(description) LIKE '%%kidney%%' OR
                                                        LOWER(description) LIKE '%%renal%%'
                                                       OR LOWER(description) LIKE '%%nephro%%' OR
                                                        LOWER(description) LIKE '%%pyelonephritis%%'
                                                       OR LOWER(description) LIKE '%%microalbuminuria%%' OR
                                                        LOWER(description) LIKE '%%proteinuria%%' THEN 1
                                                   ELSE 0 END) AS has_kidney_disease,

                                           -- MENTAL HEALTH - 12.77%
                                           MAX(
                                                   CASE
                                                       WHEN LOWER(description) LIKE '%%depress%%'
                                                           OR LOWER(description) LIKE '%%anxiety%%'
                                                           OR LOWER(description) LIKE '%%schizophrenia%%'
                                                           OR LOWER(description) LIKE '%%ptsd%%'
                                                           OR LOWER(description) LIKE '%%posttraumatic%%'
                                                           OR LOWER(description) LIKE '%%suicid%%'
                                                           OR LOWER(description) LIKE '%%bipolar%%'
                                                           OR LOWER(description) LIKE '%%attention deficit%%'
                                                           THEN 1
                                                       ELSE 0
                                                       END
                                           )                   AS has_mental_health,

                                           -- HEART DISEASE
                                           MAX(CASE
                                                   WHEN (LOWER(description) LIKE '%%heart failure%%'
                                                       OR LOWER(description) LIKE '%%myocardial infarction%%'
                                                       OR LOWER(description) LIKE '%%coronary%%'
                                                       OR LOWER(description) LIKE '%%cardiac arrest%%'
                                                       OR LOWER(description) LIKE '%%atrial fibrillation%%'
                                                       OR LOWER(description) LIKE '%%arrhythmia%%'
                                                       OR LOWER(description) LIKE '%%angina%%'
                                                       OR LOWER(description) LIKE '%%ischemic heart%%'
                                                       OR LOWER(description) LIKE '%%cardiomyopathy%%')
                                                       AND LOWER(description) NOT LIKE '%%family history%%' THEN 1
                                                   ELSE 0 END) AS has_heart_disease,

                                           -- CHRONIC RESPIRATORY
                                           MAX(CASE
                                                   WHEN (LOWER(description) LIKE '%%copd%%'
                                                       OR LOWER(description) LIKE '%%chronic obstructive%%'
                                                       OR LOWER(description) LIKE '%%emphysema%%'
                                                       OR LOWER(description) LIKE '%%chronic bronchitis%%'
                                                       OR LOWER(description) LIKE '%%asthma%%'
                                                       OR LOWER(description) LIKE '%%pulmonary fibrosis%%')
                                                       AND LOWER(description) NOT LIKE '%%family history%%' THEN 1
                                                   ELSE 0 END) AS has_chronic_resp,

                                           -- ACTIVE ACUTE RESPIRATORY (still open: end_date IS NULL)
                                           MAX(CASE
                                                   WHEN (LOWER(description) LIKE '%%acute bronchitis%%'
                                                       OR LOWER(description) LIKE '%%pneumonia%%'
                                                       OR LOWER(description) LIKE '%%acute respiratory%%'
                                                       OR LOWER(description) LIKE '%%acute upper respiratory%%'
                                                       OR LOWER(description) LIKE '%%influenza%%'
                                                       OR LOWER(description) LIKE '%%bronchiolitis%%')
                                                       AND end_date IS NULL THEN 1
                                                   ELSE 0 END) AS has_active_acute_resp
                                    FROM condition
                                    GROUP BY patient_id)
            SELECT patient_id,
                   has_diabetes,
                   has_hypertension,
                   has_heart_disease,
                   has_cancer,
                   has_kidney_disease,
                   has_mental_health,
                   CASE
                       WHEN has_chronic_resp = 1 AND has_active_acute_resp = 1 THEN 'Chronic with Active Acute'
                       WHEN has_chronic_resp = 1 THEN 'Chronic'
                       WHEN has_active_acute_resp = 1 THEN 'Active Acute'
                       ELSE 'None'
                       END AS respiratory_disease_profile
            FROM agg_conditions
            """
        ),
        con=engine,
    )

    # has_inaptient_history - 31.19%
    inpatient_history = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   MAX(CASE WHEN encounter_class = 'inpatient' THEN 1 ELSE 0 END) AS has_inpatient_history
            FROM encounter
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # is_polypharmacy - 17.71%
    medication_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(*)                                                                  AS total_medications,
                   -- NEW: is_polypharmacy flag (>=5 currently active meds, clinical standard)
                   CASE WHEN COUNT(*) FILTER (WHERE end_date IS NULL) >= 5 THEN 1 ELSE 0 END AS is_polypharmacy_raw
            FROM medication
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    procedure_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(*) AS total_procedures
            FROM "procedure"
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # Uses ILIKE patterns so it tolerates LOINC-style suffixes / casing differences
    # (e.g. "Glucose [Mass/volume] in Blood", "Body mass index (BMI)", etc.)
    observation_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   ROUND(AVG(value_norm) FILTER (WHERE desc_key = 'bmi')::numeric, 2)         AS avg_bmi,
                   ROUND(AVG(value_norm) FILTER (WHERE desc_key = 'qaly')::numeric, 2)        AS qaly,
                   ROUND(AVG(value_norm) FILTER (WHERE desc_key = 'daly')::numeric, 2)        AS daly,
                   ROUND(AVG(value_norm) FILTER (WHERE desc_key = 'systolic_bp')::numeric, 2) AS avg_systolic_bp,
                   ROUND(AVG(value_norm) FILTER (WHERE desc_key = 'glucose')::numeric, 2)     AS avg_glucose
            FROM (SELECT patient_id,
                         CASE
                             WHEN description ILIKE '%%bmi%%' OR description ILIKE '%%body mass index%%' THEN 'bmi'
            WHEN description ILIKE '%%qaly%%' THEN 'qaly'
            WHEN description ILIKE '%%daly%%' THEN 'daly'
            WHEN description ILIKE '%%systolic%%' AND description ILIKE '%%blood pressure%%' THEN 'systolic_bp'
            WHEN description ILIKE '%%glucose%%' AND description NOT ILIKE '%%urine%%' THEN 'glucose'
        END AS desc_key,
        CASE
            WHEN description ILIKE '%%glucose%%' AND units ILIKE '%%mmol%%' THEN value_numeric * 18.0
            ELSE value_numeric
        END AS value_norm,
        ROW_NUMBER() OVER (
            PARTITION BY patient_id, 
            (CASE 
                WHEN description ILIKE '%%bmi%%' OR description ILIKE '%%body mass index%%' THEN 'bmi'
                WHEN description ILIKE '%%qaly%%' THEN 'qaly'
                WHEN description ILIKE '%%daly%%' THEN 'daly'
                WHEN description ILIKE '%%systolic%%' THEN 'systolic_bp'
                WHEN description ILIKE '%%glucose%%' THEN 'glucose'
            END)
            ORDER BY date DESC
        ) AS rn
                  FROM observation
                  WHERE value_numeric IS NOT NULL
                    AND value_numeric
                      > 0
                    AND description NOT ILIKE '%%percentile%%'
                    AND description NOT ILIKE '%%z-score%%') sub
            WHERE rn <= 3 -- Redus la 3 pentru a fi mai aproape de starea curentă
              AND desc_key IS NOT NULL
              -- Filtru de siguranță pentru date aberante
              AND NOT (desc_key = 'bmi' AND value_norm > 100)
              AND NOT (desc_key = 'glucose' AND value_norm > 1000)
            GROUP BY patient_id;
            """
        ),
        con=engine,
    )

    active_conditions_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(*) AS active_conditions_count
            FROM condition
            WHERE end_date IS NULL
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # NEW: dominant careplan category - primary clinical reason patient is in the system.
    # Raw descriptions (40 values) bucketed into 9 clinical categories.
    # Allergy (0.45%), Renal (0.29%), Oncology (0.22%) merged into Other - too rare for centroids.
    # Severity-ranked careplan categorization: picks the highest-severity careplan
    # per patient rather than the most frequent. 7 clinical groups ranked 1..7.
    dominant_careplan_features = pd.read_sql(
        text(
            """
            WITH CategorizedPlans AS (SELECT patient_id,
                                             CASE
                                                 WHEN description IN (
                                                                      'Cancer care plan (record artifact)',
                                                                      'Dialysis care plan (record artifact)',
                                                                      'Terminal care (regime/therapy)'
                                                     ) THEN 'Complex, Oncology & Palliative'

                                                 WHEN description IN (
                                                     'Routine antenatal care (regime/therapy)'
                                                     ) THEN 'Maternal & Antenatal'

                                                 WHEN LOWER(description) ~ '(fracture|wound|surgery|surgical|injury|trauma|burn|musculoskeletal|spinal|jaw)'
                    THEN 'Acute Trauma, Wound & Surgery'

                                                 WHEN LOWER(description) ~ '(respiratory|asthma|pulmonary|infect|covid|pneumonia|bronchitis|sinusitis)'
                    THEN 'Respiratory & Infectious'

                                                 WHEN LOWER(description) ~ '(diabetes|hyperlipidemia|heart|hypertension|weight|cardiac|coronary)'
                    THEN 'Chronic Cardio-Metabolic'

                                                 ELSE 'General Rehab & Routine' -- Aici vor intra acum și cei cu Mental Health
                                                 END AS care_plan_category,

                                             CASE
                                                 WHEN description IN (
                                                                      'Cancer care plan (record artifact)',
                                                                      'Dialysis care plan (record artifact)',
                                                                      'Terminal care (regime/therapy)'
                                                     ) THEN 1
                                                 WHEN description IN (
                                                     'Routine antenatal care (regime/therapy)'
                                                     ) THEN 2
                                                 WHEN LOWER(description) ~ '(fracture|wound|surgery|surgical|injury|trauma|burn|musculoskeletal|spinal|jaw)' THEN 3
                                                 WHEN LOWER(description) ~ '(respiratory|asthma|pulmonary|infect|covid|pneumonia|bronchitis|sinusitis)' THEN 4
                                                 WHEN LOWER(description) ~ '(diabetes|hyperlipidemia|heart|hypertension|weight|cardiac|coronary)' THEN 5
                                                 ELSE 6 -- Rangul final pentru restul (General & Mental Health)
                                                 END AS severity_rank
                                      FROM careplan),
                 RankedPatientPlans AS (SELECT patient_id,
                                               care_plan_category,
                                               ROW_NUMBER() OVER (
               PARTITION BY patient_id
               ORDER BY severity_rank ASC
           ) AS rank_id
                                        FROM CategorizedPlans)
            SELECT patient_id, care_plan_category AS dominant_careplan
            FROM RankedPatientPlans
            WHERE rank_id = 1;
            """
        ),
        con=engine,
    )

    # distinct_providers_seen - min 1, avg 3.41, max 9
    provider_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(DISTINCT provider_id) AS distinct_providers_seen
            FROM encounter
            WHERE provider_id IS NOT NULL
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # out_of_hours_flyer - 14.47%
    ooh_features = pd.read_sql(
        text(
            """
            WITH acute AS (SELECT patient_id,
                                  EXTRACT(DOW FROM start_date)  AS dow,
                                  EXTRACT(HOUR FROM start_date) AS hr
                           FROM encounter
                           WHERE encounter_class IN ('emergency', 'urgentcare')),
                 agg AS (SELECT patient_id,
                                COUNT(*) AS total_acute,
                                SUM(CASE
                                        WHEN dow IN (0, 6) OR hr >= 20 OR hr < 8 THEN 1
                                        ELSE 0
                                    END) AS ooh_acute
                         FROM acute
                         GROUP BY patient_id)
            SELECT patient_id,
                   CASE
                       WHEN total_acute >= 5 AND (ooh_acute::float / total_acute) >= 0.8 THEN 'Yes'
                       ELSE 'No'
                       END AS out_of_hours_flyer
            FROM agg
            """
        ),
        con=engine,
    )

    # substance_use_profile: No/Low Risk - 74.04%, Moderate Risk (Alcohol) - 11.76%, High Risk (Drug/Illicit) - 14.20%
    # Derived from conditions (diagnoses) and AUDIT-C / DAST-10 screening scores.
    substance_use_features = pd.read_sql(
        text(
            """
            WITH condition_flags AS (SELECT patient_id,
                                            MAX(CASE WHEN LOWER(description) ~ '(drug abuse|misuses drugs|opioid abuse|dependent drug)' THEN 1 ELSE 0 END) AS has_illicit,
                                            MAX(CASE WHEN LOWER(description) ~ '(alcoholism|alcohol drinking)' THEN 1 ELSE 0 END)                          AS has_alcohol
                                     FROM condition
                                     GROUP BY patient_id),
                 obs_scores AS (SELECT patient_id,
                                       MAX(value_numeric) FILTER (WHERE description ILIKE '%%DAST-10%%') AS dast10_score, MAX(value_numeric) FILTER (WHERE description ILIKE '%%AUDIT-C%%') AS audit_c_score
                                FROM observation
                                WHERE value_numeric IS NOT NULL
                                GROUP BY patient_id)
            SELECT p.patient_id,
                   CASE
                       WHEN COALESCE(c.has_illicit, 0) = 1 OR COALESCE(o.dast10_score, 0) >= 3
                           THEN 'High Risk (Drug/Illicit)'
                       WHEN COALESCE(c.has_alcohol, 0) = 1 OR COALESCE(o.audit_c_score, 0) >= 4
                           THEN 'Moderate Risk (Alcohol)'
                       ELSE 'No/Low Risk'
                       END AS substance_use_profile
            FROM patient p
                     LEFT JOIN condition_flags c ON p.patient_id = c.patient_id
                     LEFT JOIN obs_scores o ON p.patient_id = o.patient_id
            """
        ),
        con=engine,
    )

    # pain_management_tier: None - 44% / Acute/Minor = 30.46% / Chronic Non-Opioid - 12.37% / Chronic Opioid - 13.17%
    pain_management_features = pd.read_sql(
        text(
            """
            WITH pain_conds AS (SELECT patient_id,
                                       MAX(CASE WHEN LOWER(description) ~ '(chronic pain|chronic low back|chronic neck|fibromyalgia|chronic intractable)' THEN 1 ELSE 0 END) AS has_chronic_pain,
                                       MAX(CASE WHEN LOWER(description) ~ '(sprain|laceration|fracture|muscle pain|joint pain)' THEN 1 ELSE 0 END)                           AS has_acute_pain
                                FROM condition
                                GROUP BY patient_id),
                 opioid_meds AS (SELECT patient_id,
                                        MAX(CASE WHEN LOWER(description) ~ '(oxycodone|fentanyl|hydrocodone|morphine|tramadol|buprenorphine|codeine)' THEN 1 ELSE 0 END) AS has_opioid
                                 FROM medication
                                 GROUP BY patient_id)
            SELECT p.patient_id,
                   CASE
                       WHEN COALESCE(pc.has_chronic_pain, 0) = 1 AND COALESCE(om.has_opioid, 0) = 1
                           THEN 'Chronic Opioid'
                       WHEN COALESCE(pc.has_chronic_pain, 0) = 1 THEN 'Chronic Non-Opioid'
                       WHEN COALESCE(pc.has_acute_pain, 0) = 1 THEN 'Acute/Minor'
                       ELSE 'None'
                       END AS pain_management_tier
            FROM patient p
                     LEFT JOIN pain_conds pc ON p.patient_id = pc.patient_id
                     LEFT JOIN opioid_meds om ON p.patient_id = om.patient_id
            """
        ),
        con=engine,
    )

    # readmission_risk_tier: None - 81.43%, Occasional - 12.11%, Frequent - 4.26%, Super-Utilizer - 2.21%
    # Categorical feature based on clinical risk levels of 30-day hospital readmissions.
    thirty_day_readmission_features = pd.read_sql(
        text(
            """
            WITH ordered_enc AS (SELECT patient_id,
                                        start_date,
                                        LAG(end_date) OVER (PARTITION BY patient_id ORDER BY start_date) AS prev_end_date
                                 FROM encounter
                                 WHERE encounter_class IN ('inpatient', 'emergency')),
                 readmission_logic AS (SELECT patient_id,
                                              COUNT(*) FILTER (WHERE prev_end_date IS NOT NULL 
                                          AND start_date <= prev_end_date + INTERVAL '30 days') AS readm_count
                                       FROM ordered_enc
                                       GROUP BY patient_id)
            SELECT p.patient_id,
                   CASE
                       WHEN COALESCE(r.readm_count, 0) = 0 THEN '0. None'
                       WHEN r.readm_count BETWEEN 1 AND 2 THEN '1. Occasional (1-2)'
                       WHEN r.readm_count BETWEEN 3 AND 5 THEN '2. Frequent (3-5)'
                       ELSE '3. Super-Utilizer (>5)'
                       END AS readmission_risk_tier
            FROM patient p
                     LEFT JOIN readmission_logic r ON p.patient_id = r.patient_id;
            """
        ),
        con=engine,
    )

    # lifetime_medication_days: total days across all medication records.
    # Active meds (end_date IS NULL) counted as ending today so long-term therapy isn't zeroed.
    lifetime_medication_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COALESCE(SUM(CASE
                                    WHEN start_date IS NOT NULL
                                        THEN GREATEST(0,
                                                      EXTRACT(EPOCH FROM (COALESCE(end_date, CURRENT_DATE) - start_date)) /
                                                      86400)
                                    ELSE 0 END) ::int, 0) AS lifetime_medication_days
            FROM medication
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # total_encounter_duration_hours: sum of all encounter durations
    encounter_duration_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COALESCE(SUM(EXTRACT(EPOCH FROM (end_date - start_date)) / 3600), 0) ::numeric(10,1) AS total_encounter_duration_hours
            FROM encounter
            WHERE end_date IS NOT NULL
              AND start_date IS NOT NULL
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # cholesterol_risk_category: Optimal - 21.29, Borderline - 24.74, High = 5.62, Very High - 5.71, Unknown - 42.64
    # Bucketed average total cholesterol into clinical risk tiers.
    cholesterol_features = pd.read_sql(
        text(
            """
            WITH cholesterol_obs AS (SELECT patient_id,
                                            AVG(value_numeric) AS avg_cholesterol
                                     FROM observation
                                     WHERE value_numeric IS NOT NULL
                                       AND value_numeric >= 0
                                       AND description ILIKE '%%cholesterol%%'
                AND description NOT ILIKE '%%ldl%%'
                AND description NOT ILIKE '%%hdl%%'
                AND description NOT ILIKE '%%triglyceride%%'
                AND description NOT ILIKE '%%ratio%%'
            GROUP BY patient_id
                )
            SELECT p.patient_id,
                   CASE
                       WHEN c.avg_cholesterol IS NULL THEN 'Unknown'
                       WHEN c.avg_cholesterol < 170 THEN 'Optimal'
                       WHEN c.avg_cholesterol < 200 THEN 'Borderline'
                       WHEN c.avg_cholesterol < 240 THEN 'High'
                       ELSE 'Very High'
                       END AS cholesterol_risk_category
            FROM patient p
                     LEFT JOIN cholesterol_obs c ON c.patient_id = p.patient_id;
            """
        ),
        con=engine,
    )

    # pregnancy_history: Active (currently pregnant) / Past / None
    pregnancy_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   CASE
                       WHEN MAX(CASE
                                    WHEN LOWER(description) LIKE '%%normal pregnancy%%'
                                        AND end_date IS NULL THEN 1
                                    ELSE 0 END) = 1 THEN 'Active'
                       WHEN MAX(CASE
                                    WHEN LOWER(description) LIKE '%%pregnancy%%'
                                        OR LOWER(description) LIKE '%%miscarriage%%'
                                        OR LOWER(description) LIKE '%%tubal ligation%%'
                                        OR LOWER(description) LIKE '%%antenatal%%'
                                        OR LOWER(description) LIKE '%%eclampsia%%' THEN 1
                                    ELSE 0 END) = 1 THEN 'Past'
                       ELSE 'None'
                       END AS pregnancy_history
            FROM condition
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    days_since_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   EXTRACT(DAY FROM (CURRENT_DATE - MAX(end_date)))::int AS days_since_last_encounter
            FROM encounter
            WHERE end_date IS NOT NULL
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    smoking_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   CASE
                       WHEN LOWER(MAX(value)) LIKE '%daily%' OR LOWER(MAX(value)) LIKE '%current%' THEN 'current'
                       WHEN LOWER(MAX(value)) LIKE '%ex-smoker%' OR LOWER(MAX(value)) LIKE '%former%' THEN 'former'
                       ELSE 'never'
                   END AS smoking_status
            FROM observation
            WHERE description ILIKE '%tobacco smoking status%'
              AND value IS NOT NULL
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    df = patient_features.copy()

    # Merge the 21 feature frames built from SQL above. patient_features is the base
    # (already copied into df), so it is NOT re-merged here.
    for right_df in [
        encounter_features,
        dominant_encounter_features,
        condition_features,
        disease_flags,
        inpatient_history,
        medication_features,
        procedure_features,
        observation_features,
        active_conditions_features,
        dominant_careplan_features,
        provider_features,
        ooh_features,
        substance_use_features,
        pain_management_features,
        thirty_day_readmission_features,
        lifetime_medication_features,
        encounter_duration_features,
        cholesterol_features,
        pregnancy_features,
        days_since_features,
        smoking_features,
    ]:
        df = df.merge(right_df, on="patient_id", how="left")

    # --- Encounter-count aggregates ------------------------------------------------
    # 0 = "no encounters of that class", semantically correct - no imputation bias.
    for col in ["ambulatory_count", "outpatient_count", "emergency_count", "urgentcare_count",
                "wellness_count", "inpatient_count", "snf_count", "hospice_count"]:
        df[col] = df[col].fillna(0)

    df["routine_care_count"] = df["ambulatory_count"] + df["outpatient_count"]
    df["acute_care_count"] = df["emergency_count"] + df["urgentcare_count"]
    df["severe_care_count"] = df["inpatient_count"] + df["snf_count"] + df["hospice_count"]
    df["preventive_to_reactive_ratio"] = df["wellness_count"] / (df["acute_care_count"] + df["severe_care_count"] + 1)

    # Fill severity-count NaNs to 0 - needed here because several downstream
    # categorical bins (medication_intensity, condition_burden) read these raw
    # counts. The clinical_severity_score PCA is now computed inside run_kprototypes
    # so df itself stays fully unscaled.
    for col in ["total_procedures", "total_medications", "active_conditions_count"]:
        df[col] = df[col].fillna(0)

    # --- Categorical bins from sparse observation numerics -------------------------
    # Rule: NEVER mean-impute sparse numerics - the artificial values shift k-prototypes
    # centroids. Instead, we bucket raw values and route unmeasured patients to "Unknown".
    df["bmi_type"] = pd.cut(
        df["avg_bmi"],
        bins=[-float("inf"), 18.5, 25, 30, 35, 40, float("inf")],
        labels=["Underweight", "Normal", "Overweight", "Obese I", "Obese II", "Obese III"],
    ).astype(object).where(df["avg_bmi"].notna(), "Unknown").astype(str)

    df["bp_risk_category"] = pd.cut(
        df["avg_systolic_bp"],
        bins=[-float("inf"), 119.9, 139.9, float("inf")],
        labels=["Normal", "Elevated", "Hypertensive"],
    ).astype(object).where(df["avg_systolic_bp"].notna(), "Unknown").astype(str)

    # Standard fasting-glucose thresholds: <100 Normal, 100–125 Prediabetic, >=126 Diabetic.
    df["glucose_risk_category"] = pd.cut(
        df["avg_glucose"],
        bins=[-float("inf"), 99.9, 125.9, float("inf")],
        labels=["Normal", "Prediabetic", "Diabetic"],
    ).astype(object).where(df["avg_glucose"].notna(), "Unknown").astype(str)

    # qaly/daly are Synthea-complete numerics - if any NaN appears, 0 is the neutral default.
    for col in ["qaly", "daly"]:
        df[col] = df[col].fillna(0)

    # --- Categorical bins from count numerics (pre-log1p) --------------------------
    df["condition_burden"] = pd.cut(
        df["active_conditions_count"],
        bins=[-1, 3, 10, float("inf")],
        labels=["low", "medium", "high"],
        right=True,
    ).astype(str)

    df["medication_intensity"] = pd.cut(
        df["total_medications"],
        bins=[-1, 5, 20, float("inf")],
        labels=["low", "medium", "high"],
        right=True,
    ).astype(str)

    # --- Demographics and base categoricals ----------------------------------------
    df["gender"] = df["gender"].fillna("F").astype(str)
    df["marital"] = df["marital"].replace("unmarried", "S").fillna("S").astype(str)
    df["race"] = df["race"].fillna("Unknown").astype(str)
    df["ethnicity"] = df["ethnicity"].fillna("Unknown").astype(str)

    # --- Disease flags: map 0/1 -> No/Yes (k-prototypes treats them as categorical) -
    for flag in [
        "has_diabetes", "has_hypertension", "has_heart_disease", "has_cancer",
        "has_kidney_disease", "has_mental_health", "has_inpatient_history",
    ]:
        df[flag] = df[flag].fillna(0).astype(int).map({0: "No", 1: "Yes"})

    df["is_polypharmacy"] = df["is_polypharmacy_raw"].fillna(0).astype(int).map({0: "No", 1: "Yes"})

    # --- Categorical NaN fills from LEFT JOINs -------------------------------------
    df["dominant_encounter_class"] = df["dominant_encounter_class"].fillna("wellness").astype(str)
    df["dominant_careplan"] = df["dominant_careplan"].fillna("None").astype(str)
    df["respiratory_disease_profile"] = df["respiratory_disease_profile"].fillna("None").astype(str)
    df["has_respiratory_disease"] = df["respiratory_disease_profile"].apply(
        lambda x: "Yes" if x != "None" else "No"
    )
    df["substance_use_profile"] = df["substance_use_profile"].fillna("None").astype(str)
    df["pain_management_tier"] = df["pain_management_tier"].fillna("None").astype(str)
    df["readmission_risk_tier"] = df["readmission_risk_tier"].fillna("None").astype(str)
    df["cholesterol_risk_category"] = df["cholesterol_risk_category"].fillna("Unknown").astype(str)
    df["pregnancy_history"] = df["pregnancy_history"].fillna("None").astype(str)
    df["out_of_hours_flyer"] = df["out_of_hours_flyer"].fillna("No").astype(str)
    df["smoking_status"] = df["smoking_status"].fillna("never").astype(str)

    # --- Remaining numerics: fillna(0) where 0 is semantically correct --------------
    for col in ["total_conditions", "total_medications", "total_procedures",
                "active_conditions_count", "distinct_providers_seen",
                "lifetime_medication_days", "total_encounter_duration_hours",
                "days_since_last_encounter"]:
        df[col] = df[col].fillna(0)

    # Keep raw vitals for FE display - only drop the intermediate polypharmacy helper.
    # avg_bmi / avg_systolic_bp / avg_glucose stay in df so they can be passed as
    # extra_feature_cols to save_cluster_results without affecting clustering.
    df = df.drop(columns=["is_polypharmacy_raw"], errors="ignore")

    return df


def plot_elbow_kproto(
        df, numerical_cols, categorical_cols, init, scaler, title, filename, location
):
    # Mirror the transform pipeline used in run_kprototypes so the elbow curve
    # reflects the same feature space as the real clustering run.
    df_scaled = df.copy()

    for col in ["total_medications", "lifetime_medication_days", "total_encounter_duration_hours"]:
        if col in numerical_cols:
            df_scaled[col] = np.log1p(df_scaled[col].clip(lower=0).astype(float))

    if "clinical_severity_score" in numerical_cols:
        sev_cols = ["total_procedures", "total_medications", "active_conditions_count"]
        sev_input = np.log1p(df[sev_cols].clip(lower=0).values.astype(float))
        sev_standardized = StandardScaler().fit_transform(sev_input)
        df_scaled["clinical_severity_score"] = PCA(n_components=1).fit_transform(sev_standardized)[:, 0]

    df_scaled[numerical_cols] = scaler.fit_transform(df_scaled[numerical_cols].values)

    all_cols = numerical_cols + categorical_cols
    matrix = df_scaled[all_cols].to_numpy()

    cat_positions = list(
        range(len(numerical_cols), len(numerical_cols) + len(categorical_cols))
    )

    costs = []
    K = range(2, 10)
    for k in K:
        kproto = KPrototypes(n_clusters=k, init=init, random_state=42, n_jobs=-1)
        kproto.fit(matrix, categorical=cat_positions)
        costs.append(kproto.cost_)
        print(f"k={k} cost={kproto.cost_}")

    plt.figure(figsize=(8, 5))
    plt.plot(K, costs, marker="o", linewidth=2)
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Cost")
    plt.title(f"Elbow Method (K-Prototypes) - {title}")
    plt.grid(True, alpha=1)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("saved elbow plot")


# def plot_umap_scatter(df_mixed, numerical_cols, categorical_cols, clusters, title, filename, location):
#     import umap
#
#     # We pass the entire dataframe because _fast_gower_matrix expects the raw df
#     # along with the column lists to do its own internal ranging/encoding.
#     df_feat = df_mixed.copy()
#
#     print("  Computing Gower distance matrix for UMAP (~1.9 GB RAM for 22k patients)...")
#     dist_matrix = _fast_gower_matrix(df_feat, numerical_cols, categorical_cols)
#
#     # Run UMAP explicitly telling it to use our precomputed Gower matrix
#     print("  Running UMAP on precomputed Gower distances...")
#     coords = umap.UMAP(
#         n_components=2,
#         metric='precomputed',
#         n_neighbors=50,  # 50-100 helps pull global clinical profiles together
#         min_dist=0.5,  # 0.5 prevents identical points from overlapping into a single dot
#         random_state=42
#     ).fit_transform(dist_matrix)
#
#     plt.figure(figsize=(10, 7))
#     scatter = plt.scatter(
#         coords[:, 0],
#         coords[:, 1],
#         c=clusters,
#         cmap="tab10",
#         alpha=1,
#         s=30,
#         edgecolors="k",
#         linewidths=0.3,
#     )
#     plt.legend(*scatter.legend_elements(), title="Cluster")
#     plt.xlabel("UMAP 1 (Gower Space)")
#     plt.ylabel("UMAP 2 (Gower Space)")
#     plt.title(f"UMAP Scatter (Gower) - {title}")
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#     plt.savefig(location / filename, dpi=150)
#     plt.close()
#     print("  saved umap scatter")


def plot_famd_scatter(df_mixed, numerical_cols, categorical_cols, clusters, title, filename, location):
    import prince

    df_feat = df_mixed[numerical_cols + categorical_cols].copy()
    for col in numerical_cols:
        df_feat[col] = df_feat[col].astype(float)
    for col in categorical_cols:
        df_feat[col] = df_feat[col].astype(str)

    famd = prince.FAMD(n_components=2, random_state=42)
    famd = famd.fit(df_feat)
    coords = famd.transform(df_feat).values  # shape (n, 2)

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        coords[:, 0],
        coords[:, 1],
        c=clusters,
        cmap="tab10",
        alpha=1,
        s=30,
        edgecolors="k",
        linewidths=0.3,
    )
    plt.legend(*scatter.legend_elements(), title="Cluster")
    plt.xlabel("Dim 1")
    plt.ylabel("Dim 2")
    plt.title(f"FAMD Scatter - {title}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("saved famd scatter")

def plot_cluster_heatmap(df, feature_cols, title, filename, location):
    cluster_means = df.groupby("cluster")[feature_cols].mean()
    cluster_normalized = (cluster_means - cluster_means.mean()) / cluster_means.std()

    plt.figure(figsize=(14, 6))
    sns.heatmap(
        cluster_normalized,
        annot=True,
        fmt=".2f",
        cmap="RdYlBu_r",
        xticklabels=feature_cols,
        yticklabels=[f"Cluster {i}" for i in cluster_means.index],
        linewidths=0.5,
    )
    plt.title(f"Cluster (normalized) - {title}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print("saved heatmap")


def plot_cluster_bars(df, feature_cols, title, filename, location):
    cluster_means = df.groupby("cluster")[feature_cols].mean()
    n_features = len(feature_cols)
    cols = 4
    rows = (n_features + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 3.5))
    axes = axes.flatten()

    colors = [plt.cm.tab10(i) for i in range(len(cluster_means))]

    for i, col in enumerate(feature_cols):
        cluster_means[col].plot(kind="bar", ax=axes[i], color=colors)
        axes[i].set_title(col, fontsize=10)
        axes[i].set_xlabel("Cluster")
        axes[i].tick_params(axis="x", rotation=0)

    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("saved bar chart")


def plot_categorical_distribution(df, categorical_cols, title, filename, location):
    n_features = len(categorical_cols)
    cols = 4
    rows = (n_features + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 4))
    axes = axes.flatten()

    for i, col in enumerate(categorical_cols):
        crosstab = pd.crosstab(df["cluster"], df[col], normalize="index")
        crosstab.plot(
            kind="bar", stacked=True, ax=axes[i], colormap="tab10", legend=True
        )
        axes[i].set_title(col, fontsize=10)
        axes[i].set_xlabel("Cluster")
        axes[i].set_ylabel("Proportion")
        axes[i].legend(fontsize=7, loc="upper right")
        axes[i].tick_params(axis="x", rotation=0)

    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(f"Categorical Distribution - {title}", fontsize=14)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("saved categorical distribution")


def run_kprototypes(
        df,
        numerical_cols,
        categorical_cols,
        init,
        scaler,
        n_clusters,
        version_name,
        location,
        gamma=None,
        random_state=42,
        elbow_plot="off",
):
    if not os.path.exists(location):
        os.makedirs(location)

    _css_raw = {"total_procedures", "total_medications", "active_conditions_count"}
    if "clinical_severity_score" in numerical_cols and _css_raw & set(numerical_cols):
        raise ValueError(
            f"{version_name}: clinical_severity_score and its raw inputs "
            f"({_css_raw & set(numerical_cols)}) are both in numerical_cols - "
            "this double-counts severity variance."
        )

    print(f"\nrunning {version_name}")
    tag = version_name.lower()
    for ch in [" ", "(", ")", "|", "=", "+", ",", ":", ";", "/", "\\", "*", "?", '"', "<", ">"]:
        tag = tag.replace(ch, "_")
    while "__" in tag:
        tag = tag.replace("__", "_")
    tag = tag.strip("_")

    # df_work stays RAW: it's what we return for the LLM prompt, DB persistence,
    # and the FE. All clustering-only transforms (log1p, severity PCA, scaler)
    # are applied to df_scaled, which is only used to build the clustering matrix.
    df_work = df.copy()
    df_scaled = df_work.copy()

    # log1p the three skewed count columns (only if the config uses them).
    skewed_count_cols = [
        "total_medications",
        "lifetime_medication_days",
        "total_encounter_duration_hours",
    ]
    for col in skewed_count_cols:
        if col in numerical_cols:
            df_scaled[col] = np.log1p(df_scaled[col].clip(lower=0).astype(float))

    # Derive clinical_severity_score from raw severity counts when the config
    # includes it. We ALSO write it to df_work so plots / FE / features JSONB
    # still have the value - it's a standardized PCA score by construction, so
    # "unscaled" doesn't apply; raw severity inputs (total_procedures,
    # total_medications, active_conditions_count) remain in df_work for the LLM.
    if "clinical_severity_score" in numerical_cols:
        sev_cols = ["total_procedures", "total_medications", "active_conditions_count"]
        sev_input = np.log1p(df_work[sev_cols].clip(lower=0).values.astype(float))
        sev_standardized = StandardScaler().fit_transform(sev_input)
        sev_pca = PCA(n_components=1)
        css = sev_pca.fit_transform(sev_standardized)[:, 0]
        print(f"clinical_severity_score PCA explained variance ratio: {sev_pca.explained_variance_ratio_[0]:.4f}")
        df_work["clinical_severity_score"] = css
        df_scaled["clinical_severity_score"] = css

    # Scale all numerical features except clinical_severity_score, which is
    # already a StandardScaler+PCA z-score - re-scaling it with a second scaler
    # would distort its meaning without adding information.
    cols_to_scale = [c for c in numerical_cols if c != "clinical_severity_score"]
    if cols_to_scale:
        df_scaled[cols_to_scale] = scaler.fit_transform(df_scaled[cols_to_scale].values)

    # Build X_num_scaled from the full numerical block (used for evaluation metrics).
    X_num_scaled = df_scaled[numerical_cols].values.astype(np.float64)

    # Build the clustering matrix. Numerical columns are cast to float64 first,
    # then categorical columns appended as strings - avoids a mixed object array
    # that slows down the KPrototypes Cython backend.
    num_matrix = df_scaled[numerical_cols].to_numpy(dtype=np.float64)
    cat_matrix = df_scaled[categorical_cols].astype(str).to_numpy()
    matrix = np.concatenate([num_matrix, cat_matrix], axis=1)

    cat_positions = list(
        range(len(numerical_cols), len(numerical_cols) + len(categorical_cols))
    )

    if elbow_plot == "on":
        plot_elbow_kproto(
            df_work,
            numerical_cols,
            categorical_cols,
            init,
            scaler,
            version_name,
            f"elbow_{tag}.png",
            location,
        )
        return None, None, None, None, None

    kproto = KPrototypes(n_clusters=n_clusters, init=init, random_state=random_state, n_jobs=-1, gamma=gamma)

    clusters = kproto.fit_predict(matrix, categorical=cat_positions)

    gamma_automat = kproto.gamma
    if isinstance(gamma_automat, dict):
        def flatten_gamma(d):
            values = []
            for v in d.values():
                if isinstance(v, dict):
                    values.extend(flatten_gamma(v))
                else:
                    values.append(v)
            return values
        gamma_values = flatten_gamma(gamma_automat)
        gamma_automat = float(np.mean(gamma_values))
    else:
        gamma_automat = float(gamma_automat)
    print(f"auto gamma is: {gamma_automat}")

    df_work["cluster"] = clusters

    print(f"converged in {kproto.n_iter_} iterations, cost={kproto.cost_:.2f}")

    plot_famd_scatter(df_work, numerical_cols, categorical_cols, clusters, version_name, f"famd_{tag}.png", location)

    plot_cluster_heatmap(
        df_work, numerical_cols, version_name, f"heatmap_{tag}.png", location
    )

    plot_cluster_bars(df_work, numerical_cols, version_name, f"bar_{tag}.png", location)

    plot_categorical_distribution(
        df_work, categorical_cols, version_name, f"categorical_{tag}.png", location
    )

    print(f"\ncluster sizes:\n{df_work['cluster'].value_counts().sort_index()}")
    print(
        f"\nnumerical means:\n{df_work.groupby('cluster')[numerical_cols].mean().round(2)}"
    )
    for cat in categorical_cols:
        print(f"\n{cat}:")
        print(pd.crosstab(df_work["cluster"], df_work[cat], normalize="index").round(2))

    cost_val = kproto.cost_
    if isinstance(cost_val, dict):
        cost_val = sum(cost_val.values())
    return df_work, X_num_scaled, clusters, float(cost_val), gamma_automat


def remove_outliers_zscore(df, threshold=4):
    # Compute z-scores per column, skipping zero-variance columns so they don't poison every row with NaN.
    cols = [c for c in OUTLIER_NUMERICAL_FEATURES if c in df.columns]
    data = df[cols].to_numpy(dtype=float)

    # log1p the skewed count cols internally so their heavy right tails don't
    # blow z-scores up and flag half the cohort as outliers.
    for i, col in enumerate(cols):
        if col in _SKEWED_OUTLIER_COLS:
            data[:, i] = np.log1p(np.clip(data[:, i], 0, None))

    mask = np.ones(len(df), dtype=bool)
    for i, col in enumerate(cols):
        col_vals = data[:, i]
        std = np.nanstd(col_vals)
        if std == 0 or np.isnan(std):
            continue
        z = np.abs((col_vals - np.nanmean(col_vals)) / std)
        mask &= z < threshold

    print(f"\nRemoved {(~mask).sum()} outliers out of {len(df)} patients")

    df_cleaned = df[mask].reset_index(drop=True)
    df_outliers = df[~mask].reset_index(drop=True)
    return df_cleaned, df_outliers


def get_clusters_summary(df_clustered, df_outliers, engine):
    # Combine clustered data and outliers for metric calculation
    df_outliers_temp = df_outliers.copy()
    df_outliers_temp['cluster'] = -1
    df_all = pd.concat([df_clustered, df_outliers_temp], ignore_index=True)

    # Pull top conditions/meds/encounters per cluster for the LLM prompt
    conditions = pd.read_sql(text("SELECT patient_id, description FROM condition"), con=engine)
    conditions = conditions.merge(df_all[["patient_id", "cluster"]], on="patient_id")
    top_conditions = conditions.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    medications = pd.read_sql(text("SELECT patient_id, description FROM medication"), con=engine)
    medications = medications.merge(df_all[["patient_id", "cluster"]], on="patient_id")
    top_medications = medications.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    procedures = pd.read_sql(text('SELECT patient_id, description FROM "procedure"'), con=engine)
    procedures = procedures.merge(df_all[["patient_id", "cluster"]], on="patient_id")
    top_procedures = procedures.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    total_patients = len(df_all)
    clusters = sorted(df_all["cluster"].unique())  # This will now include -1

    # Build the LLM prompt with the expected output format
    prompt = f"""We clustered {len(df_clustered)} patients into groups, plus {len(df_outliers)} outlier patients.
I have summarized the data for EACH cluster below. The outliers are labeled as Cluster -1.

Your task is to write extremely brief text to fit inside small frontend UI cards.
Do NOT include any extra text, introductions, markdown formatting, or bullet points.
Do NOT use em dashes (-) anywhere in your response. Use commas or plain sentence structure instead.

Structure your response EXACTLY as a list, using the pipe character (|) to separate the fields:
[Cluster ID] | [#HexColor] | [Short Title] | [1-2 sentences Description] | [1 short sentence Insight] | [1 short sentence Recommendation]

Title rules: 2-4 words, plain everyday language that anyone can understand, no medical jargon (e.g. "Older Adults with Chronic Conditions", "Young and Healthy", "High-Need Patients").
Description rules: 1-2 short sentences in plain language, understandable by a non-medical reader, no jargon.
Insight rules: pick the MOST distinguishing signal for this cluster (dominant careplan focus, disease prevalence, polypharmacy, vitals, recency of care, or encounter mix). Use concrete numbers.
Recommendation rules: tie the action to that insight (e.g. cardiac careplan dominance -> cardiology follow-up; polypharmacy -> medication review; long gap since last visit -> outreach).

Choose a suggestive hex color for each cluster that reflects its clinical profile (e.g. red tones for high-risk, green for healthy, blue for elderly chronic, orange for moderate, purple for psychiatric, teal for maternal).
Use strong, vivid, fully-saturated colors with high contrast - avoid pastel, washed-out, or faded tones. Prefer colors like #DC2626, #16A34A, #2563EB, #D97706, #7C3AED, #0891B2. The outlier cluster (-1) should always be gray (#9CA3AF).

Example output:
[0] | #DC2626 | Older Adults with Many Conditions | Elderly patients who visit the hospital often and take many medications. | Cardiac careplan dominant, 85% hypertensive, average 12 active medications. | Coordinate cardiology follow-up and run medication reviews to reduce emergency visits.
[1] | #16A34A | Young and Healthy | Younger people who rarely need medical care. | Wellness encounters dominate and chronic disease rates are near zero. | Keep them engaged with preventive care programs.
[-1] | #9CA3AF | Unusual Cases | Patients who stand out significantly from the rest of the population. | Very high variation in procedures and resource use. | Review each case individually.

=========================================
CLUSTER DATA SUMMARIES:
=========================================
"""
    for c in clusters:
        c_df = df_all[df_all['cluster'] == c]
        c_size = len(c_df)
        c_pct = (c_size / total_patients) * 100

        # clinical_severity_score is a standardized PCA z-score (~N(0,1)) - not
        # interpretable in absolute terms, so omit it. The LLM gets the raw severity
        # inputs (total_procedures, total_medications, active_conditions_count) instead.
        mean_cols = [col for col in [
            'age', 'qaly', 'daly',
            'total_procedures', 'total_medications',
            'active_conditions_count', 'lifetime_medication_days',
            'total_encounter_duration_hours',
        ] if col in c_df.columns]
        c_means = c_df[mean_cols].mean().round(1).to_dict()

        c_cats = {
            'dominant_gender': c_df['gender'].mode()[0] if not c_df['gender'].empty else 'N/A',
            'dominant_marital': c_df['marital'].mode()[0] if 'marital' in c_df and not c_df['marital'].empty else 'N/A',
            'main_encounter_type': c_df['dominant_encounter_class'].mode()[0] if not c_df[
                'dominant_encounter_class'].empty else 'N/A',
            'dominant_careplan': c_df['dominant_careplan'].mode()[0] if 'dominant_careplan' in c_df and not c_df[
                'dominant_careplan'].empty else 'N/A',
            'diabetes_rate': f"{(c_df['has_diabetes'] == 'Yes').mean() * 100:.0f}%",
            'hypertension_rate': f"{(c_df['has_hypertension'] == 'Yes').mean() * 100:.0f}%",
            'heart_disease_rate': f"{(c_df['has_heart_disease'] == 'Yes').mean() * 100:.0f}%",
            'cancer_rate': f"{(c_df['has_cancer'] == 'Yes').mean() * 100:.0f}%" if 'has_cancer' in c_df else 'N/A',
            'polypharmacy_rate': f"{(c_df['is_polypharmacy'] == 'Yes').mean() * 100:.0f}%" if 'is_polypharmacy' in c_df else 'N/A',
            'bmi_mix': c_df['bmi_type'].value_counts(normalize=True).round(2).to_dict() if 'bmi_type' in c_df else {},
            'bp_mix': c_df['bp_risk_category'].value_counts(normalize=True).round(2).to_dict() if 'bp_risk_category' in c_df else {},
            'glucose_mix': c_df['glucose_risk_category'].value_counts(normalize=True).round(2).to_dict() if 'glucose_risk_category' in c_df else {},
            'substance_use_mix': c_df['substance_use_profile'].value_counts(normalize=True).round(2).to_dict() if 'substance_use_profile' in c_df else {},
            'readmission_mix': c_df['readmission_risk_tier'].value_counts(normalize=True).round(2).to_dict() if 'readmission_risk_tier' in c_df else {},
        }

        # Careplan mix (share of each careplan category within the cluster) so the LLM
        # can tell e.g. a cardiac-dominant cluster from a psychiatric one even when the
        # mode is the same.
        careplan_mix = (
            c_df['dominant_careplan'].value_counts(normalize=True).round(2).head(4).to_dict()
            if 'dominant_careplan' in c_df else {}
        )

        c_cond = top_conditions[top_conditions['cluster'] == c]['description'].head(4).tolist()
        c_meds = top_medications[top_medications['cluster'] == c]['description'].head(3).tolist()
        c_proc = top_procedures[top_procedures['cluster'] == c]['description'].head(3).tolist()

        prompt += f"\n### DATA FOR CLUSTER {c} ({c_size} patients, {c_pct:.1f}% of total) ###\n"
        prompt += f"- Key Averages: {c_means}\n"
        prompt += f"- Demographics & Disease Rates: {c_cats}\n"
        prompt += f"- Careplan Mix (share of patients): {careplan_mix}\n"
        prompt += f"- Top Conditions: {c_cond}\n"
        prompt += f"- Top Medications: {c_meds}\n"
        prompt += f"- Top Procedures: {c_proc}\n"

    return ask_ai(prompt)


if __name__ == "__main__":
    load_dotenv()

    from db import engine as db_engine, SessionLocal
    from configs import CONFIGS

    df = build_patient_features(db_engine)

    # SCALERS = ["robust", "standard", "minmax"]
    SCALERS = ["minmax"]
    # GAMMAS = [None, 0.07, 0.13, 0.17]
    GAMMAS = [None]
    # RANDOM_STATES = [7, 42, 100]
    RANDOM_STATES = [42]
    # THRESHOLDS = [4, 6]
    THRESHOLDS = [6]
    ELBOW_PLOT = "on"

    _SCALER_MAP = {
        "minmax": MinMaxScaler(),
        "robust": RobustScaler(),
        "standard": StandardScaler(),
    }

    general_rows = []

    RESULTS_FOLDER = current_folder / "outputs"
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    general_xlsx_path = RESULTS_FOLDER / "general_conclusion_1.xlsx"


    def flush_general_conclusion():
        new_df = pd.DataFrame(general_rows)
        if general_xlsx_path.exists():
            try:
                existing = pd.read_excel(general_xlsx_path)
            except Exception as e:
                print(f"  [!] Could not read existing {general_xlsx_path.name} ({e}); overwriting")
                existing = pd.DataFrame()
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        combined = combined.drop_duplicates(subset=["version", "scaler", "gamma", "random_state", "threshold", "k"], keep="last")
        combined = combined.sort_values(["version", "scaler", "gamma", "random_state", "threshold", "k"]).reset_index(drop=True)
        combined.to_excel(general_xlsx_path, index=False)


    K_RANGES = [4]  # flat list of k values to run

    for threshold in THRESHOLDS:
        df_cleaned, df_outliers = remove_outliers_zscore(df, threshold=threshold)
        print(
            f"\nthreshold={threshold}: {len(df_cleaned)} patients after outlier removal "
            f"({len(df_outliers)} outliers)"
        )

        for cfg in CONFIGS:
            version_tag = f"v{cfg['version']}"
            num_cols = cfg["numerical"]
            cat_cols = cfg["categorical"]
            k_values = [cfg["preferred_k"]] if "preferred_k" in cfg else K_RANGES

            version_folder = RESULTS_FOLDER / version_tag
            version_folder.mkdir(parents=True, exist_ok=True)

            with open(version_folder / "features.txt", "w", encoding="utf-8") as f:
                f.write(f"version: {version_tag}\nk range: 4..6\n\n")
                f.write(f"numerical ({len(num_cols)}):\n")
                for c in num_cols:
                    f.write(f"  - {c}\n")
                f.write(f"\ncategorical ({len(cat_cols)}):\n")
                for c in cat_cols:
                    f.write(f"  - {c}\n")

            print(f"\n{'#' * 60}\n# {version_tag}\n{'#' * 60}")
            print(f"  numerical ({len(num_cols)}): {num_cols}")
            print(f"  categorical ({len(cat_cols)}): {cat_cols}")

            for scaler_name in SCALERS:
                for gamma in GAMMAS:
                    for rs in RANDOM_STATES:
                        for k in k_values:
                            gamma_label = "auto" if gamma is None else str(gamma)
                            run_tag = f"{version_tag}_s{scaler_name}_g{gamma_label}_rs{rs}_th{threshold}_k{k}"
                            location = version_folder / run_tag
                            location.mkdir(parents=True, exist_ok=True)

                            version_name = (
                                f"{run_tag} | Huang + {scaler_name} + gamma={gamma_label} + "
                                f"k={k} + seed={rs} + threshold={threshold}"
                            )
                            print(f"\n{'=' * 60}\n{version_name}\n{'=' * 60}")

                            try:
                                df_result, X_num_scaled, clusters, kproto_cost, gamma_used = run_kprototypes(
                                    df_cleaned,
                                    numerical_cols=num_cols,
                                    categorical_cols=cat_cols,
                                    scaler=_SCALER_MAP[scaler_name],
                                    init="Huang",
                                    n_clusters=k,
                                    version_name=version_name,
                                    location=location,
                                    gamma=gamma,
                                    random_state=rs,
                                    elbow_plot=ELBOW_PLOT,
                                )

                                if ELBOW_PLOT == "on":
                                    continue

                                report, eval_metrics = full_evaluation_report(
                                    df=df_result,
                                    X_numerical_scaled=X_num_scaled,
                                    clusters=clusters,
                                    numerical_cols=num_cols,
                                    categorical_cols=cat_cols,
                                )

                                metrics_row = {
                                    "kproto_cost": kproto_cost,
                                    "silhouette": eval_metrics["silhouette_score"],
                                    "gower_silhouette": eval_metrics["gower_silhouette"],
                                    "silhouette_per_cluster": eval_metrics["silhouette_per_cluster"],
                                    "calinski_harabasz": eval_metrics["calinski_harabasz_score"],
                                    "calinski_harabasz_famd": eval_metrics["calinski_harabasz_famd"],
                                    "davies_bouldin": eval_metrics["davies_bouldin_score"],
                                    "davies_bouldin_famd": eval_metrics["davies_bouldin_famd"],
                                }

                                with open(location / "conclusions.txt", "w", encoding="utf-8") as f:
                                    f.write(f"{version_name}\n{'=' * len(version_name)}\n{report}\n")

                                pd.DataFrame([{"run": version_name, **metrics_row}]).to_excel(
                                    location / "conclusions.xlsx", index=False
                                )

                                general_rows.append({
                                    "version": version_tag,
                                    "scaler": scaler_name,
                                    "gamma": gamma_label,
                                    "gamma_used": round(gamma_used, 6),
                                    "random_state": rs,
                                    "threshold": threshold,
                                    "k": k,
                                    "n_numerical": len(num_cols),
                                    "n_categorical": len(cat_cols),
                                    "numerical": ", ".join(num_cols),
                                    "categorical": ", ".join(cat_cols),
                                    **metrics_row,
                                })

                                summary_text = get_clusters_summary(df_result, df_outliers, db_engine)
                                with open(location / "llm_summary.txt", "w", encoding="utf-8") as f:
                                    f.write(summary_text)

                                fixed_image_folder = current_folder / "outputs" / "v55" / "v55_sminmax_gauto_rs42_th6_k4"
                                heatmap_path = fixed_image_folder / "heatmap_v55_sminmax_gauto_rs42_th6_k4.png"
                                famd_path = fixed_image_folder / "famd_v55_sminmax_gauto_rs42_th6_k4.png"
                                heatmap_bytes = heatmap_path.read_bytes() if heatmap_path.exists() else None
                                pca_image_bytes = famd_path.read_bytes() if famd_path.exists() else None

                                with SessionLocal() as session:
                                    save_cluster_results(
                                        db=session,
                                        df_clustered=df_result,
                                        df_outliers=df_outliers,
                                        numerical_features=num_cols,
                                        categorical_features=cat_cols,
                                        extra_feature_cols=[
                                            "avg_bmi", "avg_systolic_bp", "avg_glucose", "qaly", "daly",
                                            "days_since_last_encounter",
                                            "routine_care_count", "acute_care_count", "wellness_count",
                                            "severe_care_count", "distinct_providers_seen",
                                            "has_cancer", "has_mental_health", "is_polypharmacy", "has_respiratory_disease",
                                            "marital", "dominant_encounter_class", "smoking_status",
                                        ],
                                        n_clusters=k,
                                        params={"scaler": scaler_name, "gamma": gamma_label, "random_state": rs, "threshold": threshold},
                                        metrics=metrics_row,
                                        cluster_summaries=summary_text,
                                        heatmap_bytes=heatmap_bytes,
                                        pca_image_bytes=pca_image_bytes,
                                    )

                            except Exception as e:
                                print(f"  [!] {run_tag} failed: {e}")
                                general_rows.append({
                                    "version": version_tag,
                                    "scaler": scaler_name,
                                    "gamma": gamma_label,
                                    "random_state": rs,
                                    "threshold": threshold,
                                    "k": k,
                                    "n_numerical": len(num_cols),
                                    "n_categorical": len(cat_cols),
                                    "numerical": ", ".join(num_cols),
                                    "categorical": ", ".join(cat_cols),
                                    "error": str(e),
                                })

                                flush_general_conclusion()

    flush_general_conclusion()
    print(f"\nWrote {general_xlsx_path}")
