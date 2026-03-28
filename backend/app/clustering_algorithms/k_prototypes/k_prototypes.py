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
from dotenv import load_dotenv

from pathlib import Path

from cluster_evaluation import (
    full_evaluation_report,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    compute_general_validation,
    compute_gower_silhouette,
)

current_folder = Path(__file__).parent


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
                                                 COUNT(*) FILTER (WHERE encounter_class = 'inpatient') AS inpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'outpatient') AS outpatient_count, COUNT(*) FILTER (WHERE encounter_class = 'emergency') AS emergency_count, COUNT(*) FILTER (WHERE encounter_class = 'wellness') AS wellness_count, COUNT(*) FILTER (WHERE encounter_class = 'ambulatory') AS ambulatory_count, COUNT(*) FILTER (WHERE encounter_class = 'urgentcare') AS urgentcare_count
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
                                                       encounter_class AS dominant_encounter_class
                                                   FROM (
                                                       SELECT patient_id, encounter_class, COUNT (*) AS cnt
                                                       FROM encounter
                                                       GROUP BY patient_id, encounter_class
                                                       ) sub
                                                   ORDER BY patient_id, cnt DESC
                                                   """
        ),
        con=engine,
    )

    condition_features = pd.read_sql(
        text(
            """
                                          SELECT patient_id,
                                                 COUNT(*) AS total_conditions
                                          FROM condition
                                          GROUP BY patient_id
                                          """
        ),
        con=engine,
    )

    disease_flags = pd.read_sql(
        text(
            """
                                     SELECT patient_id,
                                            MAX(CASE WHEN LOWER(description) LIKE '%%diabetes%%' THEN 1 ELSE 0 END)     AS has_diabetes,
                                            MAX(CASE WHEN LOWER(description) LIKE '%%hypertension%%' THEN 1 ELSE 0 END) AS has_hypertension,
                                            MAX(CASE
                                                    WHEN LOWER(description) LIKE '%%heart%%' OR
                                                         LOWER(description) LIKE '%%coronary%%' THEN 1
                                                    ELSE 0 END)                                                         AS has_heart_disease
                                     FROM condition
                                     GROUP BY patient_id
                                     """
        ),
        con=engine,
    )

    medication_features = pd.read_sql(
        text(
            """
                                           SELECT patient_id,
                                                  COUNT(*) AS total_medications
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

    immunization_features = pd.read_sql(
        text(
            """
                                             SELECT patient_id,
                                                    COUNT(*) AS total_immunizations
                                             FROM immunization
                                             GROUP BY patient_id
                                             """
        ),
        con=engine,
    )

    observation_features = pd.read_sql(
        text(
            """
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

    smoking_features = pd.read_sql(
        text(
            """
                                        SELECT DISTINCT ON (patient_id)
                                               patient_id,
                                               value AS smoking_status
                                        FROM observation
                                        WHERE description = 'Tobacco smoking status NHIS'
                                        ORDER BY patient_id, date DESC
                                        """
        ),
        con=engine,
    )

    df = patient_features.copy()

    for right_df in [
        encounter_features,
        dominant_encounter_features,
        condition_features,
        disease_flags,
        medication_features,
        procedure_features,
        immunization_features,
        observation_features,
        active_conditions_features,
        recency_features,
        smoking_features,
    ]:
        df = df.merge(right_df, on="patient_id", how="left")

    for col in NUMERICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df["gender"] = df["gender"].fillna("F").astype(str)
    df["marital"] = df["marital"].replace("unmarried", "S").fillna("S").astype(str)

    df["dominant_encounter_class"] = df["dominant_encounter_class"].fillna("wellness").astype(str)

    df["has_diabetes"] = df["has_diabetes"].fillna(0).astype(int).map({0: "No", 1: "Yes"})
    df["has_hypertension"] = df["has_hypertension"].fillna(0).astype(int).map({0: "No", 1: "Yes"})
    df["has_heart_disease"] = df["has_heart_disease"].fillna(0).astype(int).map({0: "No", 1: "Yes"})

    df["has_obesity"] = (df["avg_bmi"] >= 30).astype(int).map({0: "No", 1: "Yes"})
    df["smoking_status"] = (
        df["smoking_status"]
        .fillna("never")
        .str.lower()
        .apply(
            lambda v: (
                "current"
                if "current" in v
                or "every day" in v
                or "some day" in v
                or "heavy" in v
                or "light" in v
                else ("former" if "former" in v else "never")
            )
        )
    )
    df["days_since_last_encounter"] = df["days_since_last_encounter"].fillna(0)

    bmi = df["avg_bmi"].fillna(0)
    df["bmi_category"] = pd.cut(
        bmi,
        bins=[-1, 18.5, 25.0, 30.0, 999],
        labels=["underweight", "normal", "overweight", "obese"],
    ).astype(str)

    df["age_group"] = pd.cut(
        df["age"],
        bins=[-1, 18, 35, 55, 75, 999],
        labels=["child", "young_adult", "middle_aged", "senior", "elderly"],
    ).astype(str)

    conditions_count = df["active_conditions_count"].fillna(0)
    df["condition_burden"] = pd.cut(
        conditions_count,
        bins=[-1, 3, 8, 15, 9999],
        labels=["low", "moderate", "high", "very_high"],
    ).astype(str)

    meds_count = df["total_medications"].fillna(0)
    df["medication_intensity"] = pd.cut(
        meds_count,
        bins=[-1, 10, 40, 100, 99999],
        labels=["low", "moderate", "high", "very_high"],
    ).astype(str)

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("unknown")

    return df


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


def plot_pca_scatter(X_numerical_scaled, clusters, title, filename, location):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_numerical_scaled)

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        X_pca[:, 0],
        X_pca[:, 1],
        c=clusters,
        cmap="tab10",
        alpha=1,
        s=30,
        edgecolors="k",
        linewidths=0.3,
    )
    plt.legend(*scatter.legend_elements(), title="Cluster")
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    plt.title(f"PCA Scatter - {title}")
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
    plt.savefig(location / filename, dpi=150)
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

    kproto = KPrototypes(n_clusters=n_clusters, init=init, random_state=random_state, n_jobs=-1, gamma=gamma)
    clusters = kproto.fit_predict(matrix, categorical=cat_positions)

    df_work["cluster"] = clusters

    print(f"converged in {kproto.n_iter_} iterations, cost={kproto.cost_:.2f}")

    plot_pca_scatter(X_num_scaled, clusters, version_name, f"pca_{tag}.png", location)

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

    return df_work, X_num_scaled, clusters


def remove_outliers_zscore(df, threshold=4):
    from scipy import stats

    z_scores = np.abs(stats.zscore(df[NUMERICAL_FEATURES].values))
    mask = (z_scores < threshold).all(axis=1)

    print(f"removed {(~mask).sum()} outliers out of {len(df)} patients")
    return df[mask].reset_index(drop=True)


def interpret_clusters(df_clustered, engine, evaluation_report=""):
    conditions = pd.read_sql(text("SELECT patient_id, description FROM condition"), con=engine)
    conditions = conditions.merge(df_clustered[["patient_id", "cluster"]], on="patient_id")
    top_conditions = conditions.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    medications = pd.read_sql(text("SELECT patient_id, description FROM medication"), con=engine)
    medications = medications.merge(df_clustered[["patient_id", "cluster"]], on="patient_id")
    top_medications = medications.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    procedures = pd.read_sql(text('SELECT patient_id, description FROM "procedure"'), con=engine)
    procedures = procedures.merge(df_clustered[["patient_id", "cluster"]], on="patient_id")
    top_procedures = procedures.groupby(["cluster", "description"]).size().reset_index(name="count").sort_values(
        ["cluster", "count"], ascending=[True, False])

    total_patients = len(df_clustered)
    clusters = sorted(df_clustered["cluster"].unique())

    prompt = f"""We clustered {total_patients} patients into {len(clusters)} groups using K-Prototypes. 
I have summarized the data for EACH cluster below.

Your task is to write a business/medical interpretation for EACH cluster strictly in order (from 0 to {len(clusters) - 1}).
Do NOT mix up the cluster IDs. Base your persona descriptions ONLY on the data provided under that specific cluster's heading.

Structure your response EXACTLY like this:

## Overview
[2-3 sentences summarizing the major patient types that emerged.]

## Cluster 0 — [Your Short Label]
- **Who they are**: [Age, gender, how often they come in, how sick they are. 2-3 sentences, natural tone.]
- **What stands out**: [The metrics that make this group unique compared to the average.]
- **Conditions & treatments**: [What diseases do they have? What meds and procedures show up most?]
- **What to do about it**: [One practical recommendation.]

[... Repeat the above block for Cluster 1, Cluster 2, etc ...]

## How the clusters relate
[Short paragraph comparing them. Which are healthy/sick? Which are cheap/expensive?]

## Caveats
[1-2 sentences mentioning this is synthetic Synthea data.]

=========================================
CLUSTER DATA SUMMARIES:
=========================================
"""
    for c in clusters:
        c_df = df_clustered[df_clustered['cluster'] == c]
        c_size = len(c_df)
        c_pct = (c_size / total_patients) * 100

        c_means = c_df[['age', 'qaly', 'total_procedures', 'total_medications', 'emergency_count', 'wellness_count',
                        'active_conditions_count']].mean().round(1).to_dict()

        c_cats = {
            'dominant_gender': c_df['gender'].mode()[0],
            'diabetes_rate': f"{(c_df['has_diabetes'] == 1).mean() * 100:.0f}%",
            'hypertension_rate': f"{(c_df['has_hypertension'] == 1).mean() * 100:.0f}%",
            'heart_disease_rate': f"{(c_df['has_heart_disease'] == 1).mean() * 100:.0f}%",
            'main_encounter_type': c_df['dominant_encounter_class'].mode()[0]
        }

        c_cond = top_conditions[top_conditions['cluster'] == c]['description'].head(4).tolist()
        c_meds = top_medications[top_medications['cluster'] == c]['description'].head(3).tolist()
        c_proc = top_procedures[top_procedures['cluster'] == c]['description'].head(3).tolist()

        prompt += f"\n### DATA FOR CLUSTER {c} ({c_size} patients, {c_pct:.1f}% of total) ###\n"
        prompt += f"- Key Averages: {c_means}\n"
        prompt += f"- Demographics & Disease Rates: {c_cats}\n"
        prompt += f"- Top Conditions: {c_cond}\n"
        prompt += f"- Top Medications: {c_meds}\n"
        prompt += f"- Top Procedures: {c_proc}\n"

    prompt += f"\n=========================================\n"
    prompt += f"Overall Clustering Quality Metrics:\n{evaluation_report}\n"

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)

    print(response.text)

    with open(current_folder / "gemini_response.txt", "w") as f:
        f.write(response.text)

    return response.text


if __name__ == "__main__":
    load_dotenv()

    from db import engine as db_engine

    df = build_patient_features(db_engine)
    df_cleaned = remove_outliers_zscore(df, threshold=3.75)
    # df_cleaned = df

    print(f"{len(df_cleaned)} patients left after outlier removal")

    # n_clusters = [3, 4, 5]
    n_clusters = [3,4,5,6]

    # scalers = {
    #     "standard": StandardScaler(),
    #     "robust": RobustScaler(),
    #     "power": PowerTransformer(),
    # }

    scalers = {
        "robust": RobustScaler(),
    }

    # gammas = [None, 0.01, 0.1, 0.5, 1.0, 2.0]
    gammas = [None]
    # gammas = [None, 0.1, 0.5, 1.0, 2.0, 5.0]

    # random_states = [0, 7, 42, 99, 123]
    random_states = [42]

    output_base = current_folder / "outputs" / "kproto"

    all_reports = []
    excel_rows = []

    for scaler_name, scaler in scalers.items():
        for gamma in gammas:
            for n in n_clusters:
                for rs in random_states:
                    gamma_label = "auto" if gamma is None else str(gamma)
                    version_name = f"Huang + {scaler_name} + gamma={gamma_label} + {n} clusters + seed={rs}"
                    folder_name = f"huang-{scaler_name}-gamma{gamma_label}-{n}clusters-seed{rs}"
                    location = output_base / folder_name

                    print(f"\n{'=' * 40}")
                    print(f"{version_name}")
                    print(f"{'=' * 40}")

                    df_result, X_num_scaled, clusters = run_kprototypes(
                        df_cleaned,
                        numerical_cols=NUMERICAL_FEATURES,
                        categorical_cols=CATEGORICAL_FEATURES,
                        scaler=scaler,
                        init="Huang",
                        n_clusters=n,
                        version_name=version_name,
                        location=location,
                        gamma=gamma,
                        random_state=rs,
                    )

                    report = full_evaluation_report(
                        df=df_result,
                        X_numerical_scaled=X_num_scaled,
                        clusters=clusters,
                        numerical_cols=NUMERICAL_FEATURES,
                        categorical_cols=CATEGORICAL_FEATURES,
                    )

                    all_reports.append(f"{version_name}\n{'=' * len(version_name)}\n{report}\n")

                    gen = compute_general_validation(X_num_scaled, clusters)
                    gower_sil = compute_gower_silhouette(df_result, NUMERICAL_FEATURES, CATEGORICAL_FEATURES, clusters)

                    row = {
                        "run": version_name,
                        "gamma": gamma_label,
                        "random_state": rs,
                        "silhouette": gen["silhouette_score"],
                        "gower_silhouette": gower_sil,
                        "calinski_harabasz": gen["calinski_harabasz_score"],
                        "davies_bouldin": gen["davies_bouldin_score"],
                    }

                    excel_rows.append(row)
                    # interpret_clusters(df_result, db_engine, evaluation_report=report)

    clusters_label = "_".join(str(n) for n in n_clusters)

    with open(current_folder / f"conclusions_{clusters_label}.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_reports))

    pd.DataFrame(excel_rows).to_excel(current_folder / f"conclusions_{clusters_label}.xlsx", index=False)
