import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler, RobustScaler, PowerTransformer
from sklearn.decomposition import PCA
from kmodes.kprototypes import KPrototypes
from google import genai
from google.genai import types
from dotenv import load_dotenv

from pathlib import Path

current_folder = Path(__file__).parent

NUMERICAL_FEATURES = [
    "age",
    "inpatient_count",
    "outpatient_count",
    "emergency_count",
    "wellness_count",
    "total_medications",
    "total_procedures",
    "total_immunizations",
    "avg_bmi",
    "active_conditions_count",
    "qaly",                      # how much you lived and at what quality
    # "urgentcare_count",
    "ambulatory_count",
]

CATEGORICAL_FEATURES = [
    "gender",
    "race",
    "ethnicity",
    "marital",
    "dominant_encounter_class",
    "has_diabetes",
    "has_hypertension",
    "has_heart_disease",
]


def build_patient_features(engine) -> pd.DataFrame:
    patient_features = pd.read_sql(text("""
                                        SELECT patient_id,
                                               age,
                                               gender,
                                               race,
                                               ethnicity,
                                               marital
                                        FROM patient
                                        """), con=engine)

    encounter_features = pd.read_sql(text("""
                                          SELECT patient_id,
                                                 COUNT(*) FILTER (WHERE encounter_class = 'inpatient') AS inpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'outpatient') AS outpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'emergency') AS emergency_count, COUNT(*) FILTER (WHERE encounter_class = 'wellness') AS wellness_count, COUNT(*) FILTER (WHERE encounter_class = 'ambulatory') AS ambulatory_count, COUNT(*) FILTER (WHERE encounter_class = 'urgentcare') AS urgentcare_count
                                          FROM encounter
                                          GROUP BY patient_id
                                          """), con=engine)

    dominant_encounter_features = pd.read_sql(text("""
                                                   SELECT DISTINCT
                                                   ON (patient_id)
                                                       patient_id,
                                                       encounter_class AS dominant_encounter_class
                                                   FROM (
                                                       SELECT patient_id, encounter_class, COUNT (*) AS cnt
                                                       FROM encounter
                                                       GROUP BY patient_id, encounter_class
                                                       ) sub
                                                   ORDER BY patient_id, cnt DESC
                                                   """), con=engine)

    condition_features = pd.read_sql(text("""
                                          SELECT patient_id,
                                                 COUNT(*) AS total_conditions
                                          FROM condition
                                          GROUP BY patient_id
                                          """), con=engine)

    disease_flags = pd.read_sql(text("""
                                     SELECT patient_id,
                                            MAX(CASE WHEN LOWER(description) LIKE '%%diabetes%%' THEN 1 ELSE 0 END)     AS has_diabetes,
                                            MAX(CASE WHEN LOWER(description) LIKE '%%hypertension%%' THEN 1 ELSE 0 END) AS has_hypertension,
                                            MAX(CASE
                                                    WHEN LOWER(description) LIKE '%%heart%%' OR
                                                         LOWER(description) LIKE '%%coronary%%' THEN 1
                                                    ELSE 0 END)                                                         AS has_heart_disease
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
                                                   AVG(value_numeric) FILTER (WHERE description = 'Body Mass Index') AS avg_bmi, AVG(value_numeric) FILTER (WHERE description = 'QALY') AS qaly
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

    active_conditions_features = pd.read_sql(text("""
                                                  SELECT patient_id,
                                                         COUNT(*) AS active_conditions_count
                                                  FROM condition
                                                  WHERE end_date IS NULL
                                                  GROUP BY patient_id
                                                  """), con=engine)

    df = patient_features.copy()

    for right_df in [encounter_features, dominant_encounter_features, condition_features,
                     disease_flags, medication_features, procedure_features,
                     immunization_features, observation_features, active_conditions_features]:
        df = df.merge(right_df, on="patient_id", how="left")

    for col in NUMERICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df["marital"] = df["marital"].replace("unmarried", "S").fillna("S")
    df["dominant_encounter_class"] = df["dominant_encounter_class"].fillna("wellness")
    df["has_diabetes"] = df["has_diabetes"].fillna(0).astype(int).astype(str)
    df["has_hypertension"] = df["has_hypertension"].fillna(0).astype(int).astype(str)
    df["has_heart_disease"] = df["has_heart_disease"].fillna(0).astype(int).astype(str)

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("unknown")

    return df


def plot_elbow_kproto(df, numerical_cols, categorical_cols, init, scaler, title, filename, location):
    df_scaled = df.copy()
    df_scaled[numerical_cols] = scaler.fit_transform(df[numerical_cols].values)

    all_cols = numerical_cols + categorical_cols
    matrix = df_scaled[all_cols].to_numpy()

    cat_positions = list(range(len(numerical_cols), len(numerical_cols) + len(categorical_cols)))

    costs = []
    K = range(2, 10)
    for k in K:
        kproto = KPrototypes(n_clusters=k, init=init, random_state=42, n_jobs=-1)
        kproto.fit(matrix, categorical=cat_positions)
        costs.append(kproto.cost_)
        print(f"  k={k}, cost={kproto.cost_}")

    plt.figure(figsize=(8, 5))
    plt.plot(K, costs, marker='o', linewidth=2)
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Cost")
    plt.title(f"Elbow Method (K-Prototypes) - {title}")
    plt.grid(True, alpha=1)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved Elbow")


def plot_pca_scatter(X_numerical_scaled, clusters, title, filename, location):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_numerical_scaled)

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        X_pca[:, 0], X_pca[:, 1],
        c=clusters, cmap="tab10", alpha=1, s=30, edgecolors="k", linewidths=0.3
    )
    plt.legend(*scatter.legend_elements(), title="Cluster")
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    plt.title(f"PCA Scatter - {title}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved PCA Scatter")


def plot_cluster_heatmap(df, feature_cols, title, filename, location):
    cluster_means = df.groupby("cluster")[feature_cols].mean()
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

    colors = [plt.cm.tab10(i) for i in range(len(cluster_means))]

    for i, col in enumerate(feature_cols):
        cluster_means[col].plot(kind="bar", ax=axes[i], color=colors)
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


def plot_categorical_distribution(df, categorical_cols, title, filename, location):
    n_features = len(categorical_cols)
    cols = 4
    rows = (n_features + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 4))
    axes = axes.flatten()

    for i, col in enumerate(categorical_cols):
        crosstab = pd.crosstab(df["cluster"], df[col], normalize="index")
        crosstab.plot(kind="bar", stacked=True, ax=axes[i], colormap="tab10", legend=True)
        axes[i].set_title(col, fontsize=10)
        axes[i].set_xlabel("Cluster")
        axes[i].set_ylabel("Proportion")
        axes[i].legend(fontsize=7, loc="upper right")
        axes[i].tick_params(axis='x', rotation=0)

    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(f"Categorical Distribution - {title}", fontsize=14)
    plt.tight_layout()
    plt.savefig(location / filename, dpi=150)
    plt.close()
    print("Saved Categorical Distribution")


def run_kprototypes(df, numerical_cols, categorical_cols, init, scaler, n_clusters, version_name, location):
    if not os.path.exists(location):
        os.makedirs(location)

    print("\n" + version_name)
    tag = version_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

    # scale numerical features
    df_work = df.copy()
    X_num_scaled = scaler.fit_transform(df_work[numerical_cols].values)
    df_scaled = df_work.copy()
    df_scaled[numerical_cols] = X_num_scaled

    all_cols = numerical_cols + categorical_cols
    matrix = df_scaled[all_cols].to_numpy()

    cat_positions = list(range(len(numerical_cols), len(numerical_cols) + len(categorical_cols)))

    plot_elbow_kproto(df_work, numerical_cols, categorical_cols, init, scaler,
                      version_name, f"elbow_{tag}.png", location)

    kproto = KPrototypes(n_clusters=n_clusters, init=init, random_state=42, n_jobs=-1)
    clusters = kproto.fit_predict(matrix, categorical=cat_positions)
    df_work["cluster"] = clusters

    print(f"Converged in {kproto.n_iter_} iterations, cost: {kproto.cost_}")

    plot_pca_scatter(X_num_scaled, clusters, version_name, f"pca_{tag}.png", location)

    plot_cluster_heatmap(df_work, numerical_cols, version_name, f"heatmap_{tag}.png", location)

    plot_cluster_bars(df_work, numerical_cols, version_name, f"bar_{tag}.png", location)

    plot_categorical_distribution(df_work, categorical_cols, version_name, f"categorical_{tag}.png", location)

    print(f"\n{'-' * 20}")
    print(f"  {version_name}")
    print(f"{'-' * 20}")

    print(f"\nCluster sizes:")
    print(df_work["cluster"].value_counts().sort_index())

    print(f"\nCluster means (numerical):")
    print(df_work.groupby("cluster")[numerical_cols].mean().round(2))

    print(f"\nCluster breakdown (categorical):")
    for cat in categorical_cols:
        print(f"\n--- {cat} ---")
        print(pd.crosstab(df_work["cluster"], df_work[cat], normalize="index").round(2))

    return df_work


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


def interpret_clusters(df_clustered, engine):
    """Build a summary of clusters and send to Gemini for interpretation."""

    # 1. Numerical means per cluster
    cluster_means = df_clustered.groupby("cluster")[NUMERICAL_FEATURES].mean().round(2)

    # 2. Categorical distributions per cluster
    cat_tables = ""
    for cat in CATEGORICAL_FEATURES:
        table = pd.crosstab(df_clustered["cluster"], df_clustered[cat], normalize="index").round(2)
        cat_tables += f"\n{cat}:\n{table.to_string()}\n"

    # 3. Top 10 conditions per cluster
    conditions = pd.read_sql(text("SELECT patient_id, description FROM condition"), con=engine)
    conditions = conditions.merge(df_clustered[["patient_id", "cluster"]], on="patient_id")
    top_conditions = (
        conditions.groupby(["cluster", "description"]).size()
        .reset_index(name="count")
        .sort_values(["cluster", "count"], ascending=[True, False])
        .groupby("cluster").head(10)
    )

    # 4. Cluster sizes
    sizes = df_clustered["cluster"].value_counts().sort_index().to_string()

    # 5. Build prompt
    prompt = f"""You are a medical data analyst writing for a hospital manager who doesn't have a technical background.

Here is the clustering data:

Cluster sizes:
{sizes}

Numerical feature means per cluster:
{cluster_means.to_string()}

Categorical distributions:
{cat_tables}

Top 10 conditions per cluster:
{top_conditions.to_string(index=False)}

For each cluster write:
- Start with a line "Cluster X — Label" where Label is a 2-3 word clinical name
- Then a brief plain-language description (2-3 sentences max)
- The 2-3 features that make this cluster stand out
- One practical recommendation

Keep it concise and conversational. No markdown formatting, no bold, no headers, no bullet symbols. Write in plain paragraphs like you're explaining to a colleague over coffee."""

    # 6. Send to Gemini
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt
    )

    print(response.text)

    with open(current_folder / "gemini_response.txt", "w") as f:
        f.write(response.text)

    return response.text


if __name__ == "__main__":
    load_dotenv()

    from db import engine as db_engine

    df = build_patient_features(db_engine)
    # df.to_csv("patient_features_kproto.csv", index=False)

    df_cleaned = remove_outliers_zscore(df, threshold=3)
    print(f"Patients after outlier removal: {len(df_cleaned)} (removed {len(df) - len(df_cleaned)})")

    n_clusters = 5

    df_result = run_kprototypes(
        df_cleaned,
        numerical_cols=NUMERICAL_FEATURES,
        categorical_cols=CATEGORICAL_FEATURES,
        scaler=PowerTransformer(),
        init="Huang",
        n_clusters=n_clusters,
        version_name="KPrototypes PowerTransformer Without Outliers (Huang)",
        location=current_folder / "outputs" / "kproto" / "kprototypes-powertransformer-without-outliers-huang"
    )
    df_result.to_csv("patient_features_kproto.csv", index=False)

    # df_result1 = run_kprototypes(
    #     df_cleaned,
    #     numerical_cols=NUMERICAL_FEATURES,
    #     categorical_cols=CATEGORICAL_FEATURES,
    #     scaler=PowerTransformer(),
    #     init="Cao",
    #     n_clusters=n_clusters,
    #     version_name="KPrototypes PowerTransformer Without Outliers (Cao)",
    #     location=current_folder / "outputs" / "kproto" / "kprototypes-powertransformer-without-outliers-cao"
    # )
    #
    # df_result1.to_csv("patient_features_kproto1.csv", index=False)

    # interpret_clusters(df_result, db_engine)

    # # K-Prototypes with StandardScaler for comparison
    # run_kprototypes(
    #     df_cleaned,
    #     numerical_cols=NUMERICAL_FEATURES,
    #     categorical_cols=CATEGORICAL_FEATURES,
    #     scaler=StandardScaler(),
    #     n_clusters=n_clusters,
    #     version_name="KPrototypes StandardScaler Without Outliers",
    #     location=current_folder / "outputs" / "kproto" / "kprototypes-standardscaler-without-outliers"
    # )
    #
    # # K-Prototypes with RobustScaler for comparison
    # run_kprototypes(
    #     df_cleaned,
    #     numerical_cols=NUMERICAL_FEATURES,
    #     categorical_cols=CATEGORICAL_FEATURES,
    #     scaler=RobustScaler(),
    #     n_clusters=n_clusters,
    #     version_name="KPrototypes RobustScaler Without Outliers",
    #     location=current_folder / "outputs" / "kproto" / "kprototypes-robustscaler-without-outliers"
    # )
