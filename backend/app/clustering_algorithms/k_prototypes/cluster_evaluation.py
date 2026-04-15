import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples,
    davies_bouldin_score,
    calinski_harabasz_score,
)
import warnings

warnings.filterwarnings("ignore")

NUMERICAL_FEATURES = [
    "routine_care_count", # ambulatory (vizite la cabinet) + outpatient (vizite la cabinet spitalicesc)
    "acute_care_count", # emergency (upu, urgente) + urgentcare (urgente care nu pun viata in pericol)
    "wellness_count", # wellness encounters
    "severe_care_count", # inpatient (internare clasica) + snf (centru de recuperare) + hospice (ingrijire plaiativa)
    "age",
    "clinical_severity_score", # mix intre total_procedures, total_medications si active_conditions
    # "qaly",
    # "days_since_last_encounter",
    "distinct_providers_seen",
]

CATEGORICAL_FEATURES = [
    "bmi_type",
    "gender",
    # "has_diabetes",
    # "has_cancer",
    # "has_respiratory_disease",
    # "has_heart_disease",
    # "has_mental_health",
    "dominant_careplan",
    # "out_of_hours_flyer",
    # "bp_risk_category",
    # "marital",
    # "smoking_status"
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


def _fast_gower_matrix(df, numerical_cols, categorical_cols):
    # Vectorized Gower distance in float32. The `gower` library is pure-Python
    # per-pair and ~20-50x slower than this at n=3000. We accumulate the
    # distance matrix one feature at a time so peak memory stays at ~2 * n^2
    # float32 instead of n * n * p (which would blow past 1 GB at n=3000, p=20).
    n = len(df)
    p = len(numerical_cols) + len(categorical_cols)
    dist = np.zeros((n, n), dtype=np.float32)

    if numerical_cols:
        num_data = df[numerical_cols].to_numpy(dtype=np.float32)
        ranges = num_data.max(axis=0) - num_data.min(axis=0)
        ranges[ranges == 0] = 1.0
        for i in range(num_data.shape[1]):
            col = num_data[:, i] / ranges[i]
            dist += np.abs(col[:, None] - col[None, :])

    for col_name in categorical_cols:
        codes = pd.factorize(df[col_name].astype(str))[0].astype(np.int32)
        dist += (codes[:, None] != codes[None, :]).astype(np.float32)

    dist /= p
    return dist


def compute_gower_silhouette(df, numerical_cols, categorical_cols, clusters, max_sample=3000, random_state=42):
    # silhouette on gower distance matrix (mixed numerical + categorical).
    # Gower is O(n^2) in memory and time; for n > max_sample we stratified-
    # subsample across clusters so each cluster keeps its proportion and the
    # silhouette estimate stays unbiased. Combined with the vectorized numpy
    # gower implementation below, end-to-end cost at n=20k drops from minutes
    # to ~1-2 seconds with negligible change in the score.
    labels = np.asarray(clusters)
    unique = np.unique(labels)
    if len(unique) < 2:
        return None

    n = len(labels)
    if n > max_sample:
        rng = np.random.default_rng(random_state)
        idx_parts = []
        for c in unique:
            cluster_idx = np.where(labels == c)[0]
            take = max(30, int(round(len(cluster_idx) * max_sample / n)))
            take = min(take, len(cluster_idx))
            idx_parts.append(rng.choice(cluster_idx, size=take, replace=False))
        sample_idx = np.concatenate(idx_parts)
        sampled_df = df.iloc[sample_idx].reset_index(drop=True)
        sampled_labels = labels[sample_idx]
    else:
        sampled_df = df.reset_index(drop=True)
        sampled_labels = labels

    dist_matrix = _fast_gower_matrix(sampled_df, numerical_cols, categorical_cols)
    sil = silhouette_score(dist_matrix, sampled_labels, metric="precomputed")
    return round(sil, 4)


def compute_gower_mixed_metrics(df, numerical_cols, categorical_cols, clusters, max_sample=3000, random_state=42):
    # Compute Gower-based silhouette (global) and per-cluster silhouette from a
    # single shared distance matrix. Stratified-subsampled exactly like
    # compute_gower_silhouette so cost stays O(max_sample^2).
    labels = np.asarray(clusters)
    unique = np.unique(labels)
    if len(unique) < 2:
        return {"gower_silhouette": None, "silhouette_per_cluster": {}}

    n = len(labels)
    if n > max_sample:
        rng = np.random.default_rng(random_state)
        idx_parts = []
        for c in unique:
            cluster_idx = np.where(labels == c)[0]
            take = max(30, int(round(len(cluster_idx) * max_sample / n)))
            take = min(take, len(cluster_idx))
            idx_parts.append(rng.choice(cluster_idx, size=take, replace=False))
        sample_idx = np.concatenate(idx_parts)
        sampled_df = df.iloc[sample_idx].reset_index(drop=True)
        sampled_labels = labels[sample_idx]
    else:
        sampled_df = df.reset_index(drop=True)
        sampled_labels = labels

    dist_matrix = _fast_gower_matrix(sampled_df, numerical_cols, categorical_cols)

    # Global Gower silhouette.
    gower_sil = float(silhouette_score(dist_matrix, sampled_labels, metric="precomputed"))

    # Per-cluster silhouette: mean of per-sample silhouettes within each cluster.
    # Signals which clusters are weak (mean near 0 or negative).
    sample_sils = silhouette_samples(dist_matrix, sampled_labels, metric="precomputed")
    per_cluster = {}
    for c in unique:
        mask = sampled_labels == c
        per_cluster[int(c)] = round(float(sample_sils[mask].mean()), 4) if mask.any() else None

    return {
        "gower_silhouette": round(gower_sil, 4),
        "silhouette_per_cluster": per_cluster,
    }


def compute_famd_metrics(df, numerical_cols, categorical_cols, clusters, n_components=2, random_state=42):
    # Calinski-Harabasz and Davies-Bouldin on a FAMD embedding. Unlike the
    # numerical-only versions, this reflects both numerical and categorical
    # features in the distance space those metrics operate on.
    try:
        import prince
    except ImportError:
        return {"calinski_harabasz_famd": None, "davies_bouldin_famd": None}

    labels = np.asarray(clusters)
    if len(np.unique(labels)) < 2:
        return {"calinski_harabasz_famd": None, "davies_bouldin_famd": None}

    feat = df[list(numerical_cols) + list(categorical_cols)].copy()
    for col in numerical_cols:
        feat[col] = feat[col].astype(float)
    for col in categorical_cols:
        feat[col] = feat[col].astype(str)

    famd = prince.FAMD(n_components=n_components, random_state=random_state)
    famd = famd.fit(feat)
    coords = famd.transform(feat).values

    ch = calinski_harabasz_score(coords, labels)
    db = davies_bouldin_score(coords, labels)
    return {
        "calinski_harabasz_famd": round(float(ch), 4),
        "davies_bouldin_famd": round(float(db), 4),
    }


def compute_feature_importance(df, numerical_cols, categorical_cols, clusters):
    # Per-feature contribution to the clustering, all on a [0, 1] scale.
    # Numerical: eta-squared = between-cluster variance / total variance (ANOVA effect size).
    # Categorical: Cramér's V from a cluster x category contingency table.
    # Higher = the feature separates clusters more strongly.
    labels = np.asarray(clusters)
    if len(np.unique(labels)) < 2:
        return {"numerical": {}, "categorical": {}}

    numerical_scores = {}
    for col in numerical_cols:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        mask = ~np.isnan(values)
        v = values[mask]
        lbl = labels[mask]
        total_var = v.var()
        if total_var == 0 or len(v) == 0:
            numerical_scores[col] = 0.0
            continue
        grand_mean = v.mean()
        ss_between = 0.0
        for c in np.unique(lbl):
            group = v[lbl == c]
            if len(group) == 0:
                continue
            ss_between += len(group) * (group.mean() - grand_mean) ** 2
        ss_total = ((v - grand_mean) ** 2).sum()
        eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
        numerical_scores[col] = round(float(eta_sq), 4)

    categorical_scores = {}
    for col in categorical_cols:
        if col not in df.columns:
            continue
        table = pd.crosstab(df[col], labels)
        if table.size == 0 or table.shape[0] < 2 or table.shape[1] < 2:
            categorical_scores[col] = 0.0
            continue
        chi2, _, _, _ = chi2_contingency(table)
        n = table.to_numpy().sum()
        k = min(table.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * k)) if n > 0 and k > 0 else 0.0
        categorical_scores[col] = round(float(cramers_v), 4)

    return {"numerical": numerical_scores, "categorical": categorical_scores}


def full_evaluation_report(df, X_numerical_scaled, clusters, numerical_cols, categorical_cols):

    lines = []
    lines.append("Cluster Evaluation Report\n")

    gen = compute_general_validation(X_numerical_scaled, clusters)
    sil = gen["silhouette_score"]
    ch = gen["calinski_harabasz_score"]
    db = gen["davies_bouldin_score"]

    gower = compute_gower_mixed_metrics(df, numerical_cols, categorical_cols, clusters)
    gower_sil = gower["gower_silhouette"]
    per_cluster_sil = gower["silhouette_per_cluster"]

    famd = compute_famd_metrics(df, numerical_cols, categorical_cols, clusters)
    ch_famd = famd["calinski_harabasz_famd"]
    db_famd = famd["davies_bouldin_famd"]

    def _fmt(v, spec=".4f"):
        return format(v, spec) if v is not None else "n/a"

    lines.append(f"Silhouette Score:        {_fmt(sil)}  (numerical only, range -1 to 1, higher is better, >0.7 strong, >0.5 reasonable, >0.25 weak)")
    lines.append(f"Gower Silhouette Score:  {_fmt(gower_sil)}  (numerical + categorical, same scale as above)")
    lines.append(f"Calinski-Harabasz:       {_fmt(ch, '.2f')}  (numerical only, range 0 to inf, higher is better)")
    lines.append(f"Calinski-Harabasz (FAMD):{_fmt(ch_famd, '.2f')}  (mixed, on 2D FAMD embedding)")
    lines.append(f"Davies-Bouldin:          {_fmt(db)}  (numerical only, range 0 to inf, lower is better, <1 good, >2 poor)")
    lines.append(f"Davies-Bouldin (FAMD):   {_fmt(db_famd)}  (mixed, on 2D FAMD embedding)")
    lines.append("")
    lines.append("Per-cluster Silhouette (Gower, weak if near 0 or negative):")
    for c in sorted(per_cluster_sil.keys()):
        lines.append(f"    cluster {c:<3} {_fmt(per_cluster_sil[c])}")

    importance = compute_feature_importance(df, numerical_cols, categorical_cols, clusters)
    lines.append("")
    lines.append("Feature Importance (contribution to clustering, range 0 to 1, higher is better)")
    lines.append("  Numerical (eta-squared, between-cluster variance / total variance):")
    for col, score in sorted(importance["numerical"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"    {col:<32} {score:.4f}")
    lines.append("  Categorical (Cramer's V, association between feature and cluster label):")
    for col, score in sorted(importance["categorical"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"    {col:<32} {score:.4f}")

    report = "\n".join(lines)
    print(report)
    return report