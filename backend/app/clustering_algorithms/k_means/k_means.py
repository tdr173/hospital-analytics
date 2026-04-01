import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler, RobustScaler, PowerTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from pathlib import Path

current_folder = Path(__file__).parent

NUMERICAL_FEATURES = [
    "age",
    # "total_encounters",
    "inpatient_count",
    "outpatient_count",
    "emergency_count",
    "wellness_count",
    # "total_conditions",
    "total_medications",
    "total_procedures",
    "total_immunizations",
]

MORE_NUMERICAL_FEATURES = [
    "avg_bmi",
    # "avg_systolic_bp",
    # "avg_hemoglobin",
    # "avg_leukocytes",
]

MORE_MORE_NUMERICAL_FEATURES = [
    # "avg_encounter_duration",
    "active_conditions_count",
    # "avg_medication_duration_days",
    "qaly",
]


def build_patient_features(engine) -> pd.DataFrame:
    patient_features = pd.read_sql(text("""
                                        SELECT patient_id,
                                               age
                                        FROM patient
                                        """), con=engine)

    encounter_features = pd.read_sql(text("""
                                          SELECT patient_id,
                                                 COUNT(*) AS total_encounters,
                                                 COUNT(*)    FILTER (WHERE encounter_class = 'inpatient') AS inpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'outpatient') AS outpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'emergency') AS emergency_count, COUNT(*) FILTER (WHERE encounter_class = 'wellness') AS wellness_count
                                          FROM encounter
                                          GROUP BY patient_id
                                          """), con=engine)

    condition_features = pd.read_sql(text("""
                                          SELECT patient_id,
                                                 COUNT(*) AS total_conditions
                                          FROM condition
                                          GROUP BY patient_id
                                          """), con=engine)

    medication_features = pd.read_sql(text("""
                                           SELECT patient_id,
                                                  COUNT(*) AS total_medications
                                           FROM medication
                                           GROUP BY patient_id
                                           """), con=engine)

    procedure_features = pd.read_sql(text("""
                                          SELECT patient_id,
                                                 COUNT(*) AS total_procedures
                                          FROM "procedure"
                                          GROUP BY patient_id
                                          """), con=engine)

    immunization_features = pd.read_sql(text("""
                                             SELECT patient_id,
                                                    COUNT(*) AS total_immunizations
                                             FROM immunization
                                             GROUP BY patient_id
                                             """), con=engine)

    observation_features = pd.read_sql(text("""
                                            SELECT patient_id,
                                                   AVG(value_numeric) FILTER (WHERE description = 'Body Mass Index') AS avg_bmi, AVG(value_numeric) FILTER (WHERE description = 'QALY')            AS qaly
                                            FROM (SELECT patient_id,
                                                         description,
                                                         value_numeric,
                                                         ROW_NUMBER() OVER (PARTITION BY patient_id, description ORDER BY date DESC) AS rn
                                                  FROM observation
                                                  WHERE description IN ('Body Mass Index', 'QALY')
                                                    AND value_numeric IS NOT NULL) sub
                                            WHERE rn <= 5
                                            GROUP BY patient_id
                                            """), con=engine)

    encounter_duration_features = pd.read_sql(text("""
                                                   SELECT patient_id,
                                                          AVG(duration) AS avg_encounter_duration
                                                   FROM encounter
                                                   GROUP BY patient_id
                                                   """), con=engine)

    active_conditions_features = pd.read_sql(text("""
                                                  SELECT patient_id,
                                                         COUNT(*) AS active_conditions_count
                                                  FROM condition
                                                  WHERE end_date IS NULL
                                                  GROUP BY patient_id
                                                  """), con=engine)

    medication_duration_features = pd.read_sql(text("""
                                                    SELECT patient_id,
                                                           AVG(duration_days) AS avg_medication_duration_days
                                                    FROM medication
                                                    GROUP BY patient_id
                                                    """), con=engine)

    df = patient_features.copy()

    for right_df in [encounter_features, condition_features, medication_features,
                     procedure_features, immunization_features, observation_features,
                     encounter_duration_features, active_conditions_features, medication_duration_features]:
        df = df.merge(right_df, on="patient_id", how="left")

    df = df.fillna(0)

    return df


def plot_elbow(X, title, filename, location):
    inertias = []

    for k in range(2, 12):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inertias.append(km.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(range(2, 12), inertias, marker='o', linewidth=2)
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title(f"Elbow Method - {title}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved Elbow")


def plot_pca_scatter(X, clusters, title, filename, location):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        X_pca[:, 0], X_pca[:, 1],
        c=clusters, cmap="tab10", alpha=1, s=30, edgecolors="k", linewidths=0.3
    )

    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    plt.title(f"PCA Scatter - {title}")
    plt.colorbar(scatter, label="Cluster")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved PCA Scatter")


def plot_cluster_heatmap(df, feature_cols, title, filename, location):
    cluster_means = df.groupby("cluster")[feature_cols].mean()

    # normalize per feature (z-score across clusters)
    cluster_normalized = (cluster_means - cluster_means.mean()) / cluster_means.std()

    plt.figure(figsize=(14, 6))
    sns.heatmap(
        cluster_normalized,
        annot=True, fmt=".2f", cmap="RdYlBu_r",
        xticklabels=feature_cols,
        yticklabels=[f"Cluster {i}" for i in cluster_means.index],
        linewidths=0.5
    )
    plt.title(f"Cluster (normalized) - {title}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved Heatmap")


def plot_cluster_bars(df, feature_cols, title, filename, location):
    cluster_means = df.groupby("cluster")[feature_cols].mean()
    n_features = len(feature_cols)
    cols = 4
    rows = (n_features + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 3.5))
    axes = axes.flatten()

    for i, col in enumerate(feature_cols):
        cluster_means[col].plot(kind="bar", ax=axes[i], color=[plt.cm.tab10(i) for i in range(len(cluster_means))]
                                )
        axes[i].set_title(col, fontsize=10)
        axes[i].set_xlabel("Cluster")
        axes[i].tick_params(axis='x', rotation=0)

    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved Cluster Bars")


def run_clustering(df, feature_cols, scaler, n_clusters, version_name, location):
    if not os.path.exists(location):
        os.makedirs(location)

    print("\n" + version_name)

    features = df[feature_cols].values

    X = scaler.fit_transform(features)

    plot_elbow(X, version_name, f"elbow_{version_name.lower().replace(' ', '_')}.png", location)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X)

    plot_pca_scatter(X, df["cluster"].values, version_name, f"pca_{version_name.lower().replace(' ', '_')}.png",
                     location)

    plot_cluster_heatmap(df, feature_cols, version_name, f"heatmap_{version_name.lower().replace(' ', '_')}.png",
                         location)

    plot_cluster_bars(df, feature_cols, version_name, f"bar_{version_name.lower().replace(' ', '_')}.png", location)

    return df


def remove_outliers_zscore(df, threshold=3):
    OUTLIER_COLUMNS = [
        "age",
        "outpatient_count",
        "wellness_count",
        "total_medications",
        "total_procedures",
        "total_immunizations",
        "avg_bmi",
    ]

    from scipy import stats

    z_scores = np.abs(stats.zscore(df[OUTLIER_COLUMNS].values))
    mask = (z_scores < threshold).all(axis=1)

    print(f"Removed {(~mask).sum()} patients out of {len(df)}")
    return df[mask].reset_index(drop=True)


if __name__ == "__main__":
    from db import engine as db_engine

    df = build_patient_features(db_engine)

    feature_cols = NUMERICAL_FEATURES
    feature_cols_more = NUMERICAL_FEATURES + MORE_NUMERICAL_FEATURES
    feature_cols_all = NUMERICAL_FEATURES + MORE_NUMERICAL_FEATURES + MORE_MORE_NUMERICAL_FEATURES

    df_cleaned = remove_outliers_zscore(df)

    # n_clusters = 5 # best for V1
    n_clusters = 4  # best for V1.1
    # n_clusters = 4 # best for V2

    df_basic = df.copy()

    # # V1 - StandarScaler - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols,
    #     scaler=StandardScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic StandardScaler With Outliers",
    #     location=current_folder / "outputs" / "v1" / "Basic StandardScaler With Outliers".lower().replace(" ", "-")
    # )
    #
    # # V1 - RobustScaler - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols,
    #     scaler=RobustScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic RobustScaler With Outliers",
    #     location=current_folder / "outputs" / "v1" / "Basic RobustScaler With Outliers".lower().replace(" ", "-")
    # )
    #
    # # V1 - PowerTransformer - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols,
    #     scaler=PowerTransformer(),
    #     n_clusters=n_clusters,
    #     version_name="Basic PowerTransformer With Outliers",
    #     location=current_folder / "outputs" / "v1" / "Basic PowerTransformer With Outliers".lower().replace(" ", "-")
    # )

    # # V1.1 - StandarScaler - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols,
    #     scaler=StandardScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic StandardScaler Without Outliers",
    #     location=current_folder / "outputs" / "v1.1" / "Basic StandardScaler Without Outliers".lower().replace(" ", "-")
    # )
    #
    # # V1.1 - RobustScaler - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols,
    #     scaler=RobustScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic RobustScaler Without Outliers",
    #     location=current_folder / "outputs" / "v1.1" / "Basic RobustScaler Without Outliers".lower().replace(" ", "-")
    # )
    #
    # # V1.1 - PowerTransformer - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols,
    #     scaler=PowerTransformer(),
    #     n_clusters=n_clusters,
    #     version_name="Basic PowerTransformer Without Outliers",
    #     location=current_folder / "outputs" / "v1.1" / "Basic PowerTransformer Without Outliers".lower().replace(" ", "-")
    # )

    # # V2 - StandarScaler (More Features) - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols_more,
    #     scaler=StandardScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic StandardScaler (More Features) With Outliers",
    #     location=current_folder / "outputs" / "v2" / "Basic StandardScaler (More Features) With Outliers".lower().replace(" ", "-")
    # )
    #
    # # V2 - RobustScaler (More Features) - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols_more,
    #     scaler=RobustScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic RobustScaler (More Features) With Outliers",
    #     location=current_folder / "outputs" / "v2" / "Basic RobustScaler (More Features) With Outliers".lower().replace(" ", "-")
    # )
    #
    # # V2 - PowerTransformer - outliers not filtered
    # run_clustering(
    #     df_basic, feature_cols_more,
    #     scaler=PowerTransformer(),
    #     n_clusters=n_clusters,
    #     version_name="Basic PowerTransformer (More Features) With Outliers",
    #     location=current_folder / "outputs" / "v2" / "Basic PowerTransformer (More Features) With Outliers".lower().replace(" ", "-")
    # )

    # # V2.1 - StandarScaler (More Features) - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols_more,
    #     scaler=StandardScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic StandardScaler (More Features) Without Outliers",
    #     location=current_folder / "outputs" / "v2.1" / "Basic StandardScaler (More Features) Without Outliers".lower().replace(" ", "-")
    # )
    #
    # # V2.2 - RobustScaler (More Features) - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols_more,
    #     scaler=RobustScaler(),
    #     n_clusters=n_clusters,
    #     version_name="Basic RobustScaler (More Features) Without Outliers",
    #     location=current_folder / "outputs" / "v2.1" / "Basic RobustScaler (More Features) Without Outliers".lower().replace(" ", "-")
    # )
    #
    # # V2.3 - PowerTransformer (More Features) - outliers filtered
    # run_clustering(
    #     df_cleaned, feature_cols_more,
    #     scaler=PowerTransformer(),
    #     n_clusters=n_clusters,
    #     version_name="Basic PowerTransformer (More Features) Without Outliers",
    #     location=current_folder / "outputs" / "v2.1" / "Basic PowerTransformer (More Features) Without Outliers".lower().replace(" ", "-")
    # )

    # V3 - StandarScaler (All Features) - outliers filtered - all features
    run_clustering(
        df_cleaned, feature_cols_all,
        scaler=StandardScaler(),
        n_clusters=n_clusters,
        version_name="Basic StandardScaler (All Features) Without Outliers",
        location=current_folder / "outputs" / "v3" / "Basic StandardScaler (All Features) Without Outliers".lower().replace(
            " ", "-")
    )

    # V3 - RobustScaler (All Features) - outliers filtered
    run_clustering(
        df_cleaned, feature_cols_all,
        scaler=RobustScaler(),
        n_clusters=n_clusters,
        version_name="Basic RobustScaler (All Features) Without Outliers",
        location=current_folder / "outputs" / "v3" / "Basic RobustScaler (All Features) Without Outliers".lower().replace(
            " ", "-")
    )

    # V3 - PowerTransformer (All features) - outliers filtered
    run_clustering(
        df_cleaned, feature_cols_all,
        scaler=PowerTransformer(),
        n_clusters=n_clusters,
        version_name="Basic PowerTransformer (All Features) Without Outliers",
        location=current_folder / "outputs" / "v3" / "Basic PowerTransformer (All Features) Without Outliers".lower().replace(
            " ", "-")
    )
