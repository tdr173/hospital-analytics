import json
import re
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


def save_cluster_results(
    db: Session,
    df_clustered: pd.DataFrame,
    df_outliers: pd.DataFrame,
    numerical_features: list[str],
    categorical_features: list[str],
    n_clusters: int,
    params: dict,
    metrics: dict,
    cluster_summaries: str,
    algorithm: str = "k_prototypes",
    pca_coords_clustered: np.ndarray | None = None,
    pca_coords_outliers: np.ndarray | None = None,
    heatmap_bytes: bytes | None = None,
) -> int:
    """
    Saves a clustering run, patient results, and cluster summaries to the database.

    df_clustered     - DataFrame with 'cluster' column and all features
    df_outliers      - DataFrame of outlier patients (cluster_label = -1)
    cluster_summaries - raw Gemini response string, pipe-separated per cluster
    Returns the run_id of the saved run.
    """

    result = db.execute(
        text("""
            INSERT INTO cluster_run
                (created_at, algorithm, n_clusters, n_patients, n_outliers,
                 numerical_features, categorical_features, params, metrics, heatmap)
            VALUES
                (:created_at, :algorithm, :n_clusters, :n_patients, :n_outliers,
                 :numerical_features, :categorical_features, :params, :metrics, :heatmap)
            RETURNING id
        """),
        {
            "created_at": datetime.now(),
            "algorithm": algorithm,
            "n_clusters": n_clusters,
            "n_patients": len(df_clustered),
            "n_outliers": len(df_outliers),
            "numerical_features": json.dumps(numerical_features),
            "categorical_features": json.dumps(categorical_features),
            "params": json.dumps(params),
            "metrics": json.dumps({k: (float(v) if v is not None else None) for k, v in metrics.items()}),
            "heatmap": heatmap_bytes,
        }
    )
    run_id = result.fetchone()[0]

    all_features = numerical_features + categorical_features

    def build_rows(
        df: pd.DataFrame,
        cluster_label_col: str | None,
        is_outlier: bool,
        pca_coords: np.ndarray | None = None,
    ) -> list[dict]:
        rows = []
        for i, (_, row) in enumerate(df.iterrows()):
            features = {col: _serialize(row[col]) for col in all_features if col in row.index}
            cluster_label = int(row[cluster_label_col]) if cluster_label_col and cluster_label_col in row.index else -1
            pca_x = float(pca_coords[i, 0]) if pca_coords is not None else None
            pca_y = float(pca_coords[i, 1]) if pca_coords is not None else None
            rows.append({
                "run_id": run_id,
                "patient_id": str(row["patient_id"]),
                "cluster_label": cluster_label,
                "is_outlier": is_outlier,
                "pca_x": pca_x,
                "pca_y": pca_y,
                "features": json.dumps(features),
            })
        return rows

    insert_patient_sql = text("""
        INSERT INTO cluster_patient (run_id, patient_id, cluster_label, is_outlier, pca_x, pca_y, features)
        VALUES (:run_id, :patient_id, :cluster_label, :is_outlier, :pca_x, :pca_y, :features)
    """)

    clustered_rows = build_rows(df_clustered, "cluster", is_outlier=False, pca_coords=pca_coords_clustered)
    if clustered_rows:
        db.execute(insert_patient_sql, clustered_rows)

    outlier_rows = build_rows(df_outliers, None, is_outlier=True, pca_coords=pca_coords_outliers)
    if outlier_rows:
        db.execute(insert_patient_sql, outlier_rows)

    parsed = _parse_cluster_summaries(cluster_summaries)
    if parsed:
        db.execute(
            text("""
                INSERT INTO cluster (run_id, cluster_label, color, title, description, insight, recommendation)
                VALUES (:run_id, :cluster_label, :color, :title, :description, :insight, :recommendation)
            """),
            [{"run_id": run_id, **row} for row in parsed],
        )

    db.commit()
    print(f"Saved run_id={run_id}: {len(df_clustered)} patients + {len(df_outliers)} outliers + {len(parsed)} cluster summaries")
    return run_id


def _parse_cluster_summaries(text_response: str) -> list[dict]:
    """
    Parses Gemini's pipe-separated response into a list of dicts.
    Expected line format: [cluster_id] | Title | Description | Insight | Recommendation
    """
    rows = []
    for line in text_response.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"\[(-?\d+)\]\s*\|(.+)", line)
        if not match:
            continue
        cluster_label = int(match.group(1))
        parts = [p.strip() for p in match.group(2).split("|")]
        if len(parts) < 5:
            continue
        rows.append({
            "cluster_label": cluster_label,
            "color": parts[0] if parts[0].startswith("#") else "#006780",
            "title": parts[1],
            "description": parts[2],
            "insight": parts[3],
            "recommendation": parts[4],
        })
    return rows


def _serialize(val):
    """Convert numpy/pandas types to plain Python for JSON storage."""
    if hasattr(val, "item"):
        return val.item()
    if isinstance(val, float) and pd.isna(val):
        return None
    return val
