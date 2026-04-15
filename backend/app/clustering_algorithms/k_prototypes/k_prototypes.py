import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import prince
import seaborn as sns
from scipy import stats
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler, RobustScaler, PowerTransformer, MinMaxScaler
from sklearn.decomposition import PCA
from kmodes.kprototypes import KPrototypes
from google import genai
from dotenv import load_dotenv

from pathlib import Path

from cluster_evaluation import (
    full_evaluation_report,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    compute_general_validation,
    compute_gower_silhouette,
    compute_gower_mixed_metrics,
    compute_famd_metrics,
)
from service.lllm_sql_agent_service import ask_ai

current_folder = Path(__file__).parent

print("HERE")

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
                   COUNT(*) FILTER (WHERE encounter_class = 'inpatient')   AS inpatient_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'outpatient')  AS outpatient_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'emergency')   AS emergency_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'wellness')    AS wellness_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'ambulatory')  AS ambulatory_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'urgentcare')  AS urgentcare_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'snf')         AS snf_count,
                   COUNT(*) FILTER (WHERE encounter_class = 'hospice')     AS hospice_count
            FROM encounter GROUP BY patient_id
            """
        ),
        con=engine,
    )

    dominant_encounter_features = pd.read_sql(
        text(
            """
                                                   SELECT DISTINCT ON (patient_id)
                                                       patient_id,
                                                       CASE
                                                           WHEN encounter_class IN ('ambulatory','wellness','outpatient','emergency','urgentcare','inpatient')
                                                               THEN encounter_class
                                                           ELSE 'other'
                                                       END AS dominant_encounter_class
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

    # --- REMOVED: total_conditions (redundant with active_conditions_count below) ---
    # condition_features = pd.read_sql(
    #     text("SELECT patient_id, COUNT(*) AS total_conditions FROM condition GROUP BY patient_id"),
    #     con=engine,
    # )

    disease_flags = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   MAX(CASE WHEN LOWER(description) LIKE '%%diabetes%%' THEN 1 ELSE 0 END)                AS has_diabetes,
                   MAX(CASE WHEN LOWER(description) LIKE '%%hypertension%%' THEN 1 ELSE 0 END)             AS has_hypertension,
                   MAX(CASE WHEN LOWER(description) LIKE '%%heart%%'
                              OR LOWER(description) LIKE '%%coronary%%' THEN 1 ELSE 0 END)                 AS has_heart_disease,
                   MAX(CASE WHEN LOWER(description) LIKE '%%neoplasm%%'
                              OR LOWER(description) LIKE '%%cancer%%'
                              OR LOWER(description) LIKE '%%carcinoma%%'
                              OR LOWER(description) LIKE '%%leukemia%%'
                              OR LOWER(description) LIKE '%%lymphoma%%' THEN 1 ELSE 0 END)                 AS has_cancer,
                   MAX(CASE WHEN LOWER(description) LIKE '%%asthma%%'
                              OR LOWER(description) LIKE '%%bronchitis%%'
                              OR LOWER(description) LIKE '%%pulmonary%%'
                              OR LOWER(description) LIKE '%%covid%%'
                              OR LOWER(description) LIKE '%%coronavirus%%' THEN 1 ELSE 0 END)              AS has_respiratory_disease,
                   MAX(CASE WHEN LOWER(description) LIKE '%%kidney%%'
                              OR LOWER(description) LIKE '%%renal%%' THEN 1 ELSE 0 END)                    AS has_kidney_disease,
                   MAX(CASE WHEN LOWER(description) LIKE '%%depress%%'
                              OR LOWER(description) LIKE '%%anxiety%%'
                              OR LOWER(description) LIKE '%%schizophrenia%%'
                              OR LOWER(description) LIKE '%%ptsd%%' THEN 1 ELSE 0 END)                     AS has_mental_health
            FROM condition
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

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

    medication_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   COUNT(*) AS total_medications,
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

    # --- REMOVED: total_immunizations (weak clustering signal) ---
    # immunization_features = pd.read_sql(
    #     text("SELECT patient_id, COUNT(*) AS total_immunizations FROM immunization GROUP BY patient_id"),
    #     con=engine,
    # )

    # Uses ILIKE patterns so it tolerates LOINC-style suffixes / casing differences
    # (e.g. "Glucose [Mass/volume] in Blood", "Body mass index (BMI)", etc.)
    observation_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   AVG(value_norm) FILTER (WHERE desc_key = 'bmi')         AS avg_bmi,
                   AVG(value_norm) FILTER (WHERE desc_key = 'qaly')        AS qaly,
                   AVG(value_norm) FILTER (WHERE desc_key = 'daly')        AS daly,
                   AVG(value_norm) FILTER (WHERE desc_key = 'glucose')     AS avg_glucose,
                   -- kept for inspection; excluded from NUMERICAL_FEATURES until re-evaluated
                   AVG(value_norm) FILTER (WHERE desc_key = 'systolic_bp') AS avg_systolic_bp
            FROM (
                SELECT patient_id,
                       CASE
                           WHEN description ILIKE '%%body mass index%%'
                             OR description ILIKE '%%bmi%%'                    THEN 'bmi'
                           WHEN description ILIKE '%%qaly%%'                   THEN 'qaly'
                           WHEN description ILIKE '%%daly%%'                   THEN 'daly'
                           WHEN description ILIKE '%%systolic blood pressure%%' THEN 'systolic_bp'
                           -- Glucose: normalize mmol/L -> mg/dL (*18) to fix unit mixing
                           WHEN description ILIKE '%%glucose%%'                THEN 'glucose'
                       END AS desc_key,
                       CASE
                           WHEN description ILIKE '%%glucose%%' AND units ILIKE '%%mmol%%'
                               THEN value_numeric * 18
                           ELSE value_numeric
                       END AS value_norm,
                       ROW_NUMBER() OVER (
                           PARTITION BY patient_id, description
                           ORDER BY date DESC
                       ) AS rn
                FROM observation
                WHERE value_numeric IS NOT NULL
                  AND value_numeric > 0
                  AND (description ILIKE '%%body mass index%%'
                    OR description ILIKE '%%bmi%%'
                    OR description ILIKE '%%qaly%%'
                    OR description ILIKE '%%daly%%'
                    OR description ILIKE '%%systolic blood pressure%%'
                    OR description ILIKE '%%glucose%%')
            ) sub
            WHERE rn <= 5 AND desc_key IS NOT NULL
            GROUP BY patient_id
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

    recency_features = pd.read_sql(
        text(
            """
            SELECT patient_id,
                   (CURRENT_DATE - MAX(end_date)::date) AS days_since_last_encounter
            FROM encounter
            GROUP BY patient_id
            """
        ),
        con=engine,
    )

    # --- REMOVED: careplan counts (weak, noisy clustering signal) ---
    # careplan_features = pd.read_sql(
    #     text("""
    #         SELECT patient_id,
    #                COUNT(*) AS total_careplans,
    #                COUNT(DISTINCT description) AS n_distinct_careplans
    #         FROM careplan GROUP BY patient_id
    #     """),
    #     con=engine,
    # )

    # NEW: dominant careplan category — primary clinical reason patient is in the system.
    # Raw descriptions (40 values) bucketed into 9 clinical categories.
    # Allergy (0.45%), Renal (0.29%), Oncology (0.22%) merged into Other — too rare for centroids.
    # Severity-ranked careplan categorization: picks the highest-severity careplan
    # per patient rather than the most frequent. 7 clinical groups ranked 1..7.
    dominant_careplan_features = pd.read_sql(
        text(
            """
            WITH CategorizedPlans AS (
                SELECT patient_id,
                       CASE
                           WHEN description IN (
                               'Cancer care plan (record artifact)',
                               'Dialysis care plan (record artifact)',
                               'Terminal care (regime/therapy)'
                           ) THEN 'Complex, Oncology & Palliative'
                           WHEN description IN (
                               'Routine antenatal care (regime/therapy)'
                           ) THEN 'Maternal & Antenatal'
                           WHEN LOWER(description) LIKE '%%fracture%%'
                             OR LOWER(description) LIKE '%%wound%%'
                             OR LOWER(description) LIKE '%%surgery%%'
                             OR LOWER(description) LIKE '%%surgical%%'
                             OR LOWER(description) LIKE '%%injury%%'
                             OR LOWER(description) LIKE '%%trauma%%'
                             OR LOWER(description) LIKE '%%burn%%'
                             OR LOWER(description) LIKE '%%musculoskeletal%%'
                             OR LOWER(description) LIKE '%%spinal%%'
                             OR LOWER(description) LIKE '%%jaw%%'
                           THEN 'Acute Trauma, Wound & Surgery'
                           WHEN LOWER(description) LIKE '%%respiratory%%'
                             OR LOWER(description) LIKE '%%asthma%%'
                             OR LOWER(description) LIKE '%%pulmonary%%'
                             OR LOWER(description) LIKE '%%infect%%'
                             OR LOWER(description) LIKE '%%covid%%'
                             OR LOWER(description) LIKE '%%pneumonia%%'
                             OR LOWER(description) LIKE '%%bronchitis%%'
                             OR LOWER(description) LIKE '%%sinusitis%%'
                           THEN 'Respiratory & Infectious'
                           WHEN LOWER(description) LIKE '%%dementia%%'
                             OR LOWER(description) LIKE '%%psych%%'
                             OR LOWER(description) LIKE '%%mental%%'
                             OR LOWER(description) LIKE '%%depressive%%'
                             OR LOWER(description) LIKE '%%suicide%%'
                             OR LOWER(description) LIKE '%%behavior%%'
                             OR LOWER(description) LIKE '%%inattention%%'
                             OR LOWER(description) LIKE '%%anxiety%%'
                           THEN 'Mental Health & Cognitive'
                           WHEN LOWER(description) LIKE '%%diabetes%%'
                             OR LOWER(description) LIKE '%%hyperlipidemia%%'
                             OR LOWER(description) LIKE '%%heart%%'
                             OR LOWER(description) LIKE '%%hypertension%%'
                             OR LOWER(description) LIKE '%%weight%%'
                             OR LOWER(description) LIKE '%%cardiac%%'
                             OR LOWER(description) LIKE '%%coronary%%'
                           THEN 'Chronic Cardio-Metabolic'
                           ELSE 'General Rehab & Routine'
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
                           WHEN LOWER(description) LIKE '%%fracture%%'
                             OR LOWER(description) LIKE '%%wound%%'
                             OR LOWER(description) LIKE '%%surgery%%'
                             OR LOWER(description) LIKE '%%surgical%%'
                             OR LOWER(description) LIKE '%%injury%%'
                             OR LOWER(description) LIKE '%%trauma%%'
                             OR LOWER(description) LIKE '%%burn%%'
                             OR LOWER(description) LIKE '%%musculoskeletal%%'
                             OR LOWER(description) LIKE '%%spinal%%'
                             OR LOWER(description) LIKE '%%jaw%%'
                           THEN 3
                           WHEN LOWER(description) LIKE '%%respiratory%%'
                             OR LOWER(description) LIKE '%%asthma%%'
                             OR LOWER(description) LIKE '%%pulmonary%%'
                             OR LOWER(description) LIKE '%%infect%%'
                             OR LOWER(description) LIKE '%%covid%%'
                             OR LOWER(description) LIKE '%%pneumonia%%'
                             OR LOWER(description) LIKE '%%bronchitis%%'
                             OR LOWER(description) LIKE '%%sinusitis%%'
                           THEN 4
                           WHEN LOWER(description) LIKE '%%dementia%%'
                             OR LOWER(description) LIKE '%%psych%%'
                             OR LOWER(description) LIKE '%%mental%%'
                             OR LOWER(description) LIKE '%%depressive%%'
                             OR LOWER(description) LIKE '%%suicide%%'
                             OR LOWER(description) LIKE '%%behavior%%'
                             OR LOWER(description) LIKE '%%inattention%%'
                             OR LOWER(description) LIKE '%%anxiety%%'
                           THEN 5
                           WHEN LOWER(description) LIKE '%%diabetes%%'
                             OR LOWER(description) LIKE '%%hyperlipidemia%%'
                             OR LOWER(description) LIKE '%%heart%%'
                             OR LOWER(description) LIKE '%%hypertension%%'
                             OR LOWER(description) LIKE '%%weight%%'
                             OR LOWER(description) LIKE '%%cardiac%%'
                             OR LOWER(description) LIKE '%%coronary%%'
                           THEN 6
                           ELSE 7
                       END AS severity_rank
                FROM careplan
            ), RankedPatientPlans AS (
                SELECT patient_id, care_plan_category,
                       ROW_NUMBER() OVER (
                           PARTITION BY patient_id
                           ORDER BY severity_rank ASC
                       ) AS rank_id
                FROM CategorizedPlans
            )
            SELECT patient_id, care_plan_category AS dominant_careplan
            FROM RankedPatientPlans
            WHERE rank_id = 1
            """
        ),
        con=engine,
    )

    # NEW: care fragmentation / multi-specialty care
    speciality_features = pd.read_sql(
        text(
            """
            SELECT e.patient_id,
                   COUNT(DISTINCT p.speciality) AS distinct_specialities_seen
            FROM encounter e
            JOIN provider p ON p.provider_id = e.provider_id
            WHERE p.speciality IS NOT NULL
            GROUP BY e.patient_id
            """
        ),
        con=engine,
    )

    # distinct providers seen per patient (care continuity / fragmentation at provider level)
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

    # Out-of-hours flyer: pattern of using ER/urgent care on weekends or nights
    # (20:00-07:59). Requires >=2 acute visits to distinguish a behavioral pattern
    # from a single isolated emergency. Patients with <2 acute visits get "No"
    # after the left-merge fillna below.
    ooh_features = pd.read_sql(
        text(
            """
            WITH acute AS (
                SELECT patient_id,
                       EXTRACT(DOW  FROM start_date) AS dow,
                       EXTRACT(HOUR FROM start_date) AS hr
                FROM encounter
                WHERE encounter_class IN ('emergency', 'urgentcare')
            ),
            agg AS (
                SELECT patient_id,
                       COUNT(*) AS total_acute,
                       SUM(CASE
                             WHEN dow IN (0, 6) OR hr >= 20 OR hr < 8 THEN 1
                             ELSE 0
                           END) AS ooh_acute
                FROM acute
                GROUP BY patient_id
            )
            SELECT patient_id,
                   CASE
                     WHEN total_acute >= 2 AND (ooh_acute::float / total_acute) >= 0.4 THEN 'Yes'
                     ELSE 'No'
                   END AS out_of_hours_flyer
            FROM agg
            """
        ),
        con=engine,
    )

    smoking_features = pd.read_sql(
        text(
            """
            SELECT DISTINCT ON (patient_id)
                   patient_id,
                   value AS smoking_status
            FROM observation
            WHERE description = 'Tobacco smoking status'
            ORDER BY patient_id, date DESC
            """
        ),
        con=engine,
    )

    df = patient_features.copy()

    for right_df in [
        encounter_features,
        dominant_encounter_features,
        # condition_features,          # REMOVED - total_conditions
        disease_flags,
        inpatient_history,
        medication_features,
        procedure_features,
        # immunization_features,       # REMOVED - total_immunizations
        observation_features,
        active_conditions_features,
        recency_features,
        # careplan_features,           # REMOVED - careplan counts
        dominant_careplan_features,    # NEW - dominant_careplan
        speciality_features,           # NEW - distinct_specialities_seen (currently zero-variance, kept for reference)
        provider_features,             # NEW - distinct_providers_seen
        ooh_features,                  # NEW - out_of_hours_flyer
        smoking_features,
    ]:
        df = df.merge(right_df, on="patient_id", how="left")

    # Care-class aggregates: split utilization into 4 axes.
    for col in ["ambulatory_count", "outpatient_count", "emergency_count", "urgentcare_count",
                "wellness_count", "inpatient_count", "snf_count", "hospice_count"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    df["routine_care_count"] = df["ambulatory_count"] + df["outpatient_count"]
    df["acute_care_count"] = df["emergency_count"] + df["urgentcare_count"]
    df["severe_care_count"] = df["inpatient_count"] + df["snf_count"] + df["hospice_count"]

    # clinical_severity_score: PCA axis over 3 correlated severity counts (raw values).
    sev_cols = ["total_procedures", "total_medications", "active_conditions_count"]
    for col in sev_cols:
        df[col] = df[col].fillna(0)
    sev_scaled = StandardScaler().fit_transform(df[sev_cols].values)
    sev_pca = PCA(n_components=1)
    df["clinical_severity_score"] = sev_pca.fit_transform(sev_scaled)[:, 0]
    print(f"clinical_severity_score PCA explained variance ratio: {sev_pca.explained_variance_ratio_[0]:.4f}")

    # bmi_type: categorical BMI bucketing to avoid numerical dominance.
    # Fill NaN avg_bmi with population mean *before* cut, otherwise pd.cut produces
    # NaN, .astype(str) materializes it as the literal string "nan", and subsequent
    # .fillna does nothing (no real NaN left to fill).
    avg_bmi_filled = df["avg_bmi"].fillna(df["avg_bmi"].mean())
    df["bmi_type"] = pd.cut(
        avg_bmi_filled,
        bins=[-float("inf"), 18.5, 25, 30, 35, 40, float("inf")],
        labels=["Underweight", "Normal", "Overweight", "Obese I", "Obese II", "Obese III"],
    ).astype(str)

    # bp_risk_category: simplified 3-bucket systolic BP risk. Keep NaN as "Unknown"
    # (don't impute before the cut) so patients without BP readings land in their
    # own category instead of being forced into the mean bucket.
    df["bp_risk_category"] = pd.cut(
        df["avg_systolic_bp"],
        bins=[-float("inf"), 119.9, 139.9, float("inf")],
        labels=["Normal", "Elevated", "Hypertensive"],
    ).astype(object).where(df["avg_systolic_bp"].notna(), "Unknown").astype(str)

    # Observation-derived vitals: fill missing with global mean.
    for col in ["avg_bmi", "qaly", "daly", "avg_systolic_bp", "avg_glucose"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mean())

    # Count-based numerics: zero is semantically correct (no meds -> 0 meds).
    for col in NUMERICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df["gender"] = df["gender"].fillna("F").astype(str)
    df["marital"] = df["marital"].replace("unmarried", "S").fillna("S").astype(str)
    df["out_of_hours_flyer"] = df["out_of_hours_flyer"].fillna("No").astype(str)

    df["dominant_encounter_class"] = df["dominant_encounter_class"].fillna("wellness").astype(str)

    for flag in [
        "has_diabetes", "has_hypertension", "has_heart_disease", "has_cancer",
        "has_respiratory_disease", "has_kidney_disease", "has_mental_health",
        "has_inpatient_history",
    ]:
        df[flag] = df[flag].fillna(0).astype(int).map({0: "No", 1: "Yes"})

    df["is_polypharmacy"] = df["is_polypharmacy_raw"].fillna(0).astype(int).map({0: "No", 1: "Yes"})

    # --- REMOVED: has_obesity (double-counted avg_bmi) ---
    # df["has_obesity"] = (df["avg_bmi"] >= 30).astype(int).map({0: "No", 1: "Yes"})
    # SNOMED values: "Never smoked tobacco (finding)", "Ex-smoker (finding)", "Smokes tobacco daily (finding)"
    df["smoking_status"] = (
        df["smoking_status"]
        .fillna("Never smoked tobacco (finding)")
        .astype(str)
        .apply(
            lambda v: (
                "current" if "daily" in v.lower() or "some day" in v.lower()
                else ("former" if "ex-smoker" in v.lower() or "ex smoker" in v.lower()
                      else "never")
            )
        )
    )
    df["days_since_last_encounter"] = df["days_since_last_encounter"].fillna(0)

    # Categorical bins derived from numerical features.
    df["condition_burden"] = pd.cut(
        df["active_conditions_count"],
        bins=[-1, 3, 10, float("inf")],
        labels=["low", "medium", "high"],
        right=True,
    ).astype(str).fillna("low")

    df["medication_intensity"] = pd.cut(
        df["total_medications"],
        bins=[-1, 5, 20, float("inf")],
        labels=["low", "medium", "high"],
        right=True,
    ).astype(str).fillna("low")

    df["dominant_careplan"] = df["dominant_careplan"].fillna("none")

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("unknown")

    # Log1p-transform heavily right-skewed count features AFTER categorical bins are
    # computed (bins use raw values). Compresses tails so RobustScaler doesn't amplify
    # extreme patients into cluster-dominating outliers.
    # outpatient: max=107 vs mean=6.95; ambulatory: max=775 vs mean=29.95
    # total_medications: max=2618 vs mean=40.98; total_procedures: max=1955 vs mean=144
    for col in ["total_medications", "total_procedures", "inpatient_count", "emergency_count"]:
        if col in df.columns:
            df[col] = np.log1p(df[col])

    for col in ["routine_care_count", "acute_care_count", "wellness_count", "severe_care_count"]:
        if col in df.columns:
            df[col] = np.log1p(df[col])

    # days_since_last_encounter: max ~10 958 (30y) dominates raw. log1p compresses
    # the tail while preserving recency signal.
    if "days_since_last_encounter" in df.columns:
        df["days_since_last_encounter"] = np.log1p(df["days_since_last_encounter"].clip(lower=0))

    return df


def apply_rule_based_prefilter(df):
    # Carve off clinically obvious groups before k-prototypes sees the data.
    # These are high-precision rules: patients matching them always land in the
    # same semantic cluster anyway, and forcing k-prototypes to "discover" them
    # drags the residual silhouette down.
    #
    # Priority order matters: a patient matching multiple rules gets assigned
    # to the first matching rule (highest clinical severity first).
    #
    # Returns (rule_df, remainder_df). rule_df has a `rule_cluster` column
    # with string labels; remainder_df is what goes into k-prototypes.
    d = df.copy()
    d["rule_cluster"] = None

    palliative_mask = (
        (d["rule_cluster"].isna())
        & (d.get("dominant_careplan", "") == "Complex, Oncology & Palliative")
    )
    d.loc[palliative_mask, "rule_cluster"] = "rule_palliative_oncology"

    maternal_mask = (
        (d["rule_cluster"].isna())
        & (d.get("dominant_careplan", "") == "Maternal & Antenatal")
        & (d.get("gender", "") == "F")
    )
    d.loc[maternal_mask, "rule_cluster"] = "rule_maternal"

    if "has_cancer" in d.columns:
        oncology_mask = (d["rule_cluster"].isna()) & (d["has_cancer"] == "Yes")
        d.loc[oncology_mask, "rule_cluster"] = "rule_oncology"

    rule_df = d[d["rule_cluster"].notna()].reset_index(drop=True)
    remainder_df = d[d["rule_cluster"].isna()].drop(columns=["rule_cluster"]).reset_index(drop=True)

    print("\nRule-based prefilter:")
    if len(rule_df):
        print(rule_df["rule_cluster"].value_counts().to_string())
    print(f"  remainder for k-prototypes: {len(remainder_df)} patients")
    return rule_df, remainder_df


def plot_elbow_kproto(
    df, numerical_cols, categorical_cols, init, scaler, title, filename, location
):
    df_scaled = df.copy()
    df_scaled[numerical_cols] = scaler.fit_transform(df[numerical_cols].values)

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


def plot_pca_scatter(df_mixed, numerical_cols, categorical_cols, clusters, title, filename, location):
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
    print("saved pca scatter")


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

    print(f"\nrunning {version_name}")
    tag = version_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

    # scale numerical features
    df_work = df.copy()
    X_num_scaled = scaler.fit_transform(df_work[numerical_cols].values)
    df_scaled = df_work.copy()
    df_scaled[numerical_cols] = X_num_scaled

    all_cols = numerical_cols + categorical_cols
    matrix = df_scaled[all_cols].to_numpy()

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
        return None, None, None, None

    kproto = KPrototypes(n_clusters=n_clusters, init=init, random_state=random_state, n_jobs=-1, gamma=gamma)

    clusters = kproto.fit_predict(matrix, categorical=cat_positions)

    gamma_automat = kproto.gamma
    print(f"Valoarea gamma setată automat a fost: {gamma_automat}")

    df_work["cluster"] = clusters

    print(f"converged in {kproto.n_iter_} iterations, cost={kproto.cost_:.2f}")

    plot_pca_scatter(df_work, numerical_cols, categorical_cols, clusters, version_name, f"pca_{tag}.png", location)

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

    return df_work, X_num_scaled, clusters, float(kproto.cost_)


def remove_outliers_zscore(df, threshold=5):
    # Diagnostic: show distribution of each numerical feature so zero-variance /
    # all-NaN columns are obvious before they silently wipe every row.
    print("\nNumerical feature diagnostics:")
    for col in NUMERICAL_FEATURES:
        if col not in df.columns:
            print(f"  {col:<32} MISSING FROM DF")
            continue
        s = df[col]
        print(
            f"  {col:<32} nonnull={s.notna().sum():>6} "
            f"min={s.min():>10.2f} max={s.max():>10.2f} "
            f"mean={s.mean():>10.2f} std={s.std():>10.2f}"
        )

    # Compute z-scores per column, skipping zero-variance columns so they
    # don't poison every row with NaN.
    data = df[NUMERICAL_FEATURES].to_numpy(dtype=float)
    mask = np.ones(len(df), dtype=bool)
    skipped = []
    for i, col in enumerate(NUMERICAL_FEATURES):
        col_vals = data[:, i]
        std = np.nanstd(col_vals)
        if std == 0 or np.isnan(std):
            skipped.append(col)
            continue
        z = np.abs((col_vals - np.nanmean(col_vals)) / std)
        mask &= z < threshold

    if skipped:
        print(f"\n  Skipped zero-variance columns during outlier filter: {skipped}")

    print(f"\nRemoved {(~mask).sum()} outliers out of {len(df)} patients")

    df_cleaned = df[mask].reset_index(drop=True)
    df_outliers = df[~mask].reset_index(drop=True)
    return df_cleaned, df_outliers


def get_clusters_summary(df_clustered, df_outliers, engine, evaluation_report=""):
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
    clusters = sorted(df_all["cluster"].unique()) # This will now include -1

    # Build the LLM prompt with the expected output format
    prompt = f"""We clustered {len(df_clustered)} patients into groups, plus {len(df_outliers)} outlier patients.
I have summarized the data for EACH cluster below. The outliers are labeled as Cluster -1.

Your task is to write extremely brief text to fit inside small frontend UI cards.
Do NOT include any extra text, introductions, markdown formatting, or bullet points.
Do NOT use em dashes (—) anywhere in your response. Use commas or plain sentence structure instead.

Structure your response EXACTLY as a list, using the pipe character (|) to separate the fields:
[Cluster ID] | [#HexColor] | [Short Title] | [1-2 sentences Description] | [1 short sentence Insight] | [1 short sentence Recommendation]

Title rules: 2-4 words, plain everyday language that anyone can understand, no medical jargon (e.g. "Older Adults with Chronic Conditions", "Young and Healthy", "High-Need Patients").
Description rules: 1-2 short sentences in plain language, understandable by a non-medical reader, no jargon.
Insight rules: pick the MOST distinguishing signal for this cluster (dominant careplan focus, disease prevalence, polypharmacy, vitals, recency of care, or encounter mix). Use concrete numbers.
Recommendation rules: tie the action to that insight (e.g. cardiac careplan dominance -> cardiology follow-up; polypharmacy -> medication review; long gap since last visit -> outreach).

Choose a suggestive hex color for each cluster that reflects its clinical profile (e.g. red tones for high-risk, green for healthy, blue for elderly chronic, orange for moderate, purple for psychiatric, teal for maternal).
Use distinct, saturated colors. The outlier cluster (-1) should always be gray (#9CA3AF).

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

        mean_cols = [col for col in [
            'age', 'avg_bmi', 'qaly', 'daly',
            'avg_systolic_bp', 'avg_glucose',
            'total_procedures', 'total_medications',
            'active_conditions_count', 'days_since_last_encounter',
        ] if col in c_df.columns]
        c_means = c_df[mean_cols].mean().round(1).to_dict()

        c_cats = {
            'dominant_gender': c_df['gender'].mode()[0] if not c_df['gender'].empty else 'N/A',
            'dominant_marital': c_df['marital'].mode()[0] if 'marital' in c_df and not c_df['marital'].empty else 'N/A',
            'main_encounter_type': c_df['dominant_encounter_class'].mode()[0] if not c_df['dominant_encounter_class'].empty else 'N/A',
            'dominant_careplan': c_df['dominant_careplan'].mode()[0] if 'dominant_careplan' in c_df and not c_df['dominant_careplan'].empty else 'N/A',
            'diabetes_rate': f"{(c_df['has_diabetes'] == 'Yes').mean() * 100:.0f}%",
            'hypertension_rate': f"{(c_df['has_hypertension'] == 'Yes').mean() * 100:.0f}%",
            'heart_disease_rate': f"{(c_df['has_heart_disease'] == 'Yes').mean() * 100:.0f}%",
            'cancer_rate': f"{(c_df['has_cancer'] == 'Yes').mean() * 100:.0f}%" if 'has_cancer' in c_df else 'N/A',
            'polypharmacy_rate': f"{(c_df['is_polypharmacy'] == 'Yes').mean() * 100:.0f}%" if 'is_polypharmacy' in c_df else 'N/A',
            'smoking_mix': c_df['smoking_status'].value_counts(normalize=True).round(2).to_dict() if 'smoking_status' in c_df else {},
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

    # client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)

    # print(response.text)
    #
    # with open(current_folder / "gemini_response.txt", "w", encoding="utf-8") as f:
    #     f.write(response.text)

    # return response.text

    return ask_ai(prompt)

if __name__ == "__main__":
    load_dotenv()

    from db import engine as db_engine
    from db.db_connector import SessionLocal
    from save_results import save_cluster_results
    from sqlalchemy import text

    df = build_patient_features(db_engine)

    n_clusters = [6]

    scalers = {
        # "power": PowerTransformer(),
        # "robust": RobustScaler(),
        # "standard": StandardScaler(),
        "minmax": MinMaxScaler(),
    }

    gammas = [None]
    # gammas = [None]

    random_states = [42]
    outlier_thresholds = [4]
    ELBOW_PLOT = "off"  # "on" = elbow only (no clustering), "off" = clustering only

    output_base = current_folder / "outputs"
    output_base.mkdir(parents=True, exist_ok=True)

    all_reports = []
    excel_rows = []

    for threshold in outlier_thresholds:
        df_cleaned, df_outliers = remove_outliers_zscore(df, threshold=threshold)
        print(f"\nthreshold={threshold}: {len(df_cleaned)} patients left after outlier removal ({len(df_outliers)} outliers)")

        df_for_kproto = df_cleaned
        df_rules = df_cleaned.iloc[0:0].assign(rule_cluster=pd.Series(dtype=str))

        for scaler_name, scaler in scalers.items():
            for gamma in gammas:
                for n in n_clusters:
                    for rs in random_states:
                        gamma_label = "auto" if gamma is None else str(gamma)
                        version_name = f"Huang + {scaler_name} + gamma={gamma_label} + {n} clusters + seed={rs} + threshold={threshold}"
                        location = output_base

                        print(f"\n{'=' * 40}")
                        print(f"{version_name}")
                        print(f"{'=' * 40}")

                        df_result, X_num_scaled, clusters, kproto_cost = run_kprototypes(
                            df_for_kproto,
                            numerical_cols=NUMERICAL_FEATURES,
                            categorical_cols=CATEGORICAL_FEATURES,
                            scaler=scaler,
                            init="Huang",
                            n_clusters=n,
                            version_name=version_name,
                            location=location,
                            gamma=gamma,
                            random_state=rs,
                            elbow_plot=ELBOW_PLOT,
                        )

                        if ELBOW_PLOT == "on":
                            continue

                        report = full_evaluation_report(
                            df=df_result,
                            X_numerical_scaled=X_num_scaled,
                            clusters=clusters,
                            numerical_cols=NUMERICAL_FEATURES,
                            categorical_cols=CATEGORICAL_FEATURES,
                        )

                        all_reports.append(f"{version_name}\n{'=' * len(version_name)}\n{report}\n")

                        gen = compute_general_validation(X_num_scaled, clusters)
                        gower = compute_gower_mixed_metrics(df_result, NUMERICAL_FEATURES, CATEGORICAL_FEATURES, clusters)
                        famd_m = compute_famd_metrics(df_result, NUMERICAL_FEATURES, CATEGORICAL_FEATURES, clusters)

                        row = {
                            "run": version_name,
                            "gamma": gamma_label,
                            "random_state": rs,
                            "outlier_threshold": threshold,
                            "kproto_cost": kproto_cost,
                            "silhouette": gen["silhouette_score"],
                            "gower_silhouette": gower["gower_silhouette"],
                            "silhouette_per_cluster": gower["silhouette_per_cluster"],
                            "calinski_harabasz": gen["calinski_harabasz_score"],
                            "calinski_harabasz_famd": famd_m["calinski_harabasz_famd"],
                            "davies_bouldin": gen["davies_bouldin_score"],
                            "davies_bouldin_famd": famd_m["davies_bouldin_famd"],
                        }

                        excel_rows.append(row)

                        # Merge rule-based clusters onto k-proto results. Rule clusters get
                        # labels n, n+1, ... (after k-proto's 0..n-1). Metrics above are
                        # reported on the residual only (honest) but the saved cohort
                        # reflects the full hybrid assignment.
                        rule_label_map = {name: n + i for i, name in enumerate(sorted(df_rules["rule_cluster"].unique()))} if len(df_rules) else {}
                        if len(df_rules):
                            df_rules_labeled = df_rules.copy()
                            df_rules_labeled["cluster"] = df_rules_labeled["rule_cluster"].map(rule_label_map).astype(int)
                            df_rules_labeled = df_rules_labeled.drop(columns=["rule_cluster"])
                            df_combined = pd.concat([df_result, df_rules_labeled], ignore_index=True)
                        else:
                            df_combined = df_result
                        print(f"\nHybrid cluster map (k-proto 0..{n - 1}, rules above): {rule_label_map}")

                        lmm_summary = get_clusters_summary(df_combined, df_outliers, db_engine, evaluation_report=report)

                        # read heatmap PNG bytes
                        tag = version_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
                        heatmap_path = location / f"heatmap_{tag}.png"
                        heatmap_bytes = heatmap_path.read_bytes() if heatmap_path.exists() else None

                        # compute FAMD coords for full combined cohort + outlier patients
                        _famd = prince.FAMD(n_components=2, random_state=42)
                        _df_combined_feat = df_combined[NUMERICAL_FEATURES + CATEGORICAL_FEATURES].copy()
                        for _col in NUMERICAL_FEATURES:
                            _df_combined_feat[_col] = _df_combined_feat[_col].astype(float)
                        for _col in CATEGORICAL_FEATURES:
                            _df_combined_feat[_col] = _df_combined_feat[_col].astype(str)
                        _famd = _famd.fit(_df_combined_feat)
                        pca_coords_clustered = _famd.transform(_df_combined_feat).values
                        _df_outliers_feat = df_outliers[NUMERICAL_FEATURES + CATEGORICAL_FEATURES].copy()
                        for _col in NUMERICAL_FEATURES:
                            _df_outliers_feat[_col] = _df_outliers_feat[_col].astype(float)
                        for _col in CATEGORICAL_FEATURES:
                            _df_outliers_feat[_col] = _df_outliers_feat[_col].astype(str)
                        pca_coords_outliers = _famd.transform(_df_outliers_feat).values

                        # save to database
                        db_session = SessionLocal()
                        try:
                            save_cluster_results(
                                db=db_session,
                                df_clustered=df_combined,
                                df_outliers=df_outliers,
                                pca_coords_clustered=pca_coords_clustered,
                                pca_coords_outliers=pca_coords_outliers,
                                numerical_features=NUMERICAL_FEATURES,
                                categorical_features=CATEGORICAL_FEATURES,
                                n_clusters=n + len(rule_label_map),
                                algorithm="k_prototypes_hybrid",
                                extra_feature_cols=["qaly", "total_medications", "active_conditions_count", "condition_burden"],
                                params={
                                    "scaler": scaler_name,
                                    "gamma": gamma_label,
                                    "init": "Huang",
                                    "random_state": rs,
                                    "outlier_threshold": threshold,
                                    "rule_clusters": rule_label_map,
                                    "metrics_scope": "residual_only",
                                },
                                metrics={
                                    "silhouette": gen["silhouette_score"],
                                    "gower_silhouette": gower["gower_silhouette"],
                                    "calinski_harabasz": gen["calinski_harabasz_score"],
                                    "davies_bouldin": gen["davies_bouldin_score"],
                                },
                                cluster_summaries=lmm_summary,
                                heatmap_bytes=heatmap_bytes,
                            )
                        finally:
                            db_session.close()

    clusters_label = "_".join(str(n) for n in n_clusters)

    with open(current_folder / f"conclusions_{clusters_label}.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_reports))

    pd.DataFrame(excel_rows).to_excel(current_folder / f"conclusions_{clusters_label}.xlsx", index=False)
