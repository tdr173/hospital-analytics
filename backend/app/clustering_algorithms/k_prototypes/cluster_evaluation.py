import numpy as np
import pandas as pd
import gower
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import warnings

warnings.filterwarnings("ignore")

NUMERICAL_FEATURES = [
    "age",
    # "inpatient_count",         # number of hospital admissions (stays)
    "outpatient_count",          # number of consultations where the patient leaves the same day
    "emergency_count",           # emergency room visits
    "wellness_count",            # routine check-ups / preventive visits
    "total_medications",       # total number of prescriptions
    "total_procedures",
    # "total_immunizations",
    # "avg_bmi",                 # average of the last 5 measurements (or available ones)
    # "active_conditions_count", # number of active diseases
    "qaly",                      # Quality-Adjusted Life Year (1 = perfect health for one year)
    "ambulatory_count",          # scheduled visits for monitoring/specialty care
    # "days_since_last_encounter",
]

CATEGORICAL_FEATURES = [
    "gender",
    # "race",
    # "ethnicity",
    "dominant_encounter_class", # wellness, ambulatory, outpatient..
    #"has_heart_disease",
    # "smoking_status",
    "bmi_category",             # underweight, normal, overweight, obese
    "age_group",                # child, young_adult, middle_aged, senior, elderly
    "condition_burden",         # low, moderate, high, very_high
    "medication_intensity",     # low, moderate, high, very_high
    "has_hypertension",
    "has_diabetes",
    # "marital",
]


def compute_general_validation(X_numerical_scaled, clusters):
    n_clusters = len(np.unique(clusters))
    if n_clusters < 2:
        return {
            "silhouette_score": None,
            "calinski_harabasz_score": None,
            "davies_bouldin_score": None,
        }

    # silhouette: -1 to 1, higher is better, >0.7 strong, >0.5 reasonable, >0.25 weak
    # measures "how well" an element fits in its cluster
    sil = silhouette_score(X_numerical_scaled, clusters)

    # calinski-harabasz: 0 to inf, higher is better
    # measures the ratio between of how far the clusters are and how dispersed the points are within clusters
    # shows if the clusters are compact and separated
    ch = calinski_harabasz_score(X_numerical_scaled, clusters)

    # davies-bouldin: 0 to inf, lower is better, <1 good, >2 poor
    # shows how similar the clusters are, if they massively overlap
    db = davies_bouldin_score(X_numerical_scaled, clusters)

    return {
        "silhouette_score": round(sil, 4),
        "calinski_harabasz_score": round(ch, 4),
        "davies_bouldin_score": round(db, 4),
    }


def compute_gower_silhouette(df, numerical_cols, categorical_cols, clusters):
    # silhouette on gower distance matrix (mixed numerical + categorical)
    n_clusters = len(np.unique(clusters))
    if n_clusters < 2:
        return None

    mixed_df = df[numerical_cols + categorical_cols].copy()
    cat_mask = [False] * len(numerical_cols) + [True] * len(categorical_cols)
    dist_matrix = gower.gower_matrix(mixed_df, cat_features=cat_mask)
    sil = silhouette_score(dist_matrix, clusters, metric="precomputed")
    return round(sil, 4)


def full_evaluation_report(df, X_numerical_scaled, clusters, numerical_cols, categorical_cols):

    lines = []
    lines.append("Cluster Evaluation Report\n")

    gen = compute_general_validation(X_numerical_scaled, clusters)
    sil = gen["silhouette_score"]
    ch = gen["calinski_harabasz_score"]
    db = gen["davies_bouldin_score"]

    gower_sil = compute_gower_silhouette(df, numerical_cols, categorical_cols, clusters)

    lines.append(f"Silhouette Score:        {sil:.4f}  (numerical only, range -1 to 1, higher is better, >0.7 strong, >0.5 reasonable, >0.25 weak)")
    lines.append(f"Gower Silhouette Score:  {gower_sil:.4f}  (numerical + categorical, same scale as above)")
    lines.append(f"Calinski-Harabasz:       {ch:.2f}  (range 0 to inf, higher is better)")
    lines.append(f"Davies-Bouldin:          {db:.4f}  (range 0 to inf, lower is better, <1 good, >2 poor)")

    report = "\n".join(lines)
    print(report)
    return report