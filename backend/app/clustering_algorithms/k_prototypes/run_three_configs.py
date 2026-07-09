"""Driver: run v60, v40, v55 in order, AI-interpret each cluster, persist + export.

For each config (in order v60 -> v40 -> v55):
  1. run K-Prototypes with the config's features + preferred_k (minmax, gamma auto,
     random_state=42, threshold=6 - matching the benchmark parameters)
  2. evaluate + LLM cluster summaries + save_cluster_results (wipes+writes the DB)
  3. call ClusterService.get_ai_analysis for every cluster label (incl. -1 outlier),
     which computes and persists cluster.ai_analysis
  4. export the full cluster table (with ai_analysis) + meta to outputs/ai_dumps/vXX.json
     BEFORE the next run overwrites it.

Because save_cluster_results TRUNCATEs the tables on each run, only the LAST config
(v55) remains in the DB. The JSON dumps preserve v60 and v40.

Run:  .venv/Scripts/python.exe app/clustering_algorithms/k_prototypes/run_three_configs.py
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/app

from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text

from clustering_algorithms.k_prototypes.k_prototypes import (
    build_patient_features,
    remove_outliers_zscore,
    run_kprototypes,
    get_clusters_summary,
    current_folder,
)
from clustering_algorithms.k_prototypes.cluster_evaluation import full_evaluation_report
from clustering_algorithms.k_prototypes.save_results import save_cluster_results

# fixed benchmark parameters (from the spreadsheet screenshot)
SCALER_NAME = "minmax"
GAMMA = None
GAMMA_LABEL = "auto"
RS = 42
THRESHOLD = 6

# run order: v60, then v40, then v55 (v55 last => v55 stays in the DB)
CONFIGS_TO_RUN = [
    {
        "version": 60,
        "preferred_k": 6,
        "numerical": [
            "age",
            "active_conditions_count",
            "total_medications",
            "preventive_to_reactive_ratio",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_heart_disease",
            "has_diabetes",
            "has_hypertension",
            "condition_burden",
            "bmi_type",
            "cholesterol_risk_category",
        ],
    },
    {
        "version": 40,
        "preferred_k": 5,
        "numerical": [
            "age",
            "active_conditions_count",
            "total_medications",
            "lifetime_medication_days",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_heart_disease",
            "has_diabetes",
            "has_hypertension",
            "condition_burden",
            "bmi_type",
            "cholesterol_risk_category",
        ],
    },
    {
        "version": 55,
        "preferred_k": 4,
        "numerical": [
            "age",
            "active_conditions_count",
            "total_medications",
            "total_procedures",
            "preventive_to_reactive_ratio",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_heart_disease",
            "has_diabetes",
            "has_hypertension",
            "condition_burden",
            "bmi_type",
            "dominant_careplan",
        ],
    },
]

EXTRA_FEATURE_COLS = [
    "avg_bmi", "avg_systolic_bp", "avg_glucose", "qaly", "daly",
    "days_since_last_encounter",
    "routine_care_count", "acute_care_count", "wellness_count",
    "severe_care_count", "distinct_providers_seen",
    "has_cancer", "has_mental_health", "is_polypharmacy", "has_respiratory_disease",
    "marital", "dominant_encounter_class", "smoking_status",
]


def _export_cluster_table(session, path: Path, version_tag: str, extra: dict):
    rows = session.execute(text(
        "SELECT id, cluster_label, color, title, description, insight, "
        "recommendation, ai_analysis, created_at FROM cluster ORDER BY cluster_label"
    )).mappings().all()
    meta = session.execute(text(
        "SELECT algorithm, n_clusters, n_patients, n_outliers, numerical_features, "
        "categorical_features, params, metrics, created_at FROM cluster_meta"
    )).mappings().first()

    payload = {
        "version": version_tag,
        **extra,
        "cluster_meta": dict(meta) if meta else None,
        "clusters": [dict(r) for r in rows],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    print(f"  exported {len(rows)} cluster rows -> {path}")


def main():
    load_dotenv()
    from db import engine, SessionLocal
    from repository import ClusterRepository
    from service import ClusterService

    print("building patient features (once) ...")
    df = build_patient_features(engine)

    # outlier removal uses a fixed feature list -> identical for every config
    df_cleaned, df_outliers = remove_outliers_zscore(df, threshold=THRESHOLD)
    print(
        f"threshold={THRESHOLD}: {len(df_cleaned)} patients after outlier removal "
        f"({len(df_outliers)} outliers)"
    )

    dumps_dir = current_folder / "outputs" / "ai_dumps"

    for cfg in CONFIGS_TO_RUN:
        version_tag = f"v{cfg['version']}"
        num_cols = cfg["numerical"]
        cat_cols = cfg["categorical"]
        k = cfg["preferred_k"]

        run_tag = f"{version_tag}_s{SCALER_NAME}_g{GAMMA_LABEL}_rs{RS}_th{THRESHOLD}_k{k}"
        location = current_folder / "outputs" / version_tag / run_tag
        location.mkdir(parents=True, exist_ok=True)
        version_name = (
            f"{run_tag} | Huang + {SCALER_NAME} + gamma={GAMMA_LABEL} + "
            f"k={k} + seed={RS} + threshold={THRESHOLD}"
        )

        print(f"\n{'#' * 70}\n# {version_tag}  (k={k}, expecting {k}+1 clusters)\n{'#' * 70}")

        df_result, X_num_scaled, clusters, kproto_cost, gamma_used = run_kprototypes(
            df_cleaned,
            numerical_cols=num_cols,
            categorical_cols=cat_cols,
            scaler=MinMaxScaler(),
            init="Huang",
            n_clusters=k,
            version_name=version_name,
            location=location,
            gamma=GAMMA,
            random_state=RS,
            elbow_plot="off",
        )

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

        print(f"  generating LLM cluster summaries for {version_tag} ...")
        summary_text = get_clusters_summary(df_result, df_outliers, engine)
        with open(location / "llm_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary_text)

        # use this run's own rendered images (not a fixed v55 folder)
        heatmap_path = next(location.glob("heatmap_*.png"), None)
        famd_path = next(location.glob("famd_*.png"), None)
        heatmap_bytes = heatmap_path.read_bytes() if heatmap_path else None
        pca_image_bytes = famd_path.read_bytes() if famd_path else None

        with SessionLocal() as session:
            save_cluster_results(
                db=session,
                df_clustered=df_result,
                df_outliers=df_outliers,
                numerical_features=num_cols,
                categorical_features=cat_cols,
                extra_feature_cols=EXTRA_FEATURE_COLS,
                n_clusters=k,
                params={"scaler": SCALER_NAME, "gamma": GAMMA_LABEL, "random_state": RS, "threshold": THRESHOLD},
                metrics=metrics_row,
                cluster_summaries=summary_text,
                heatmap_bytes=heatmap_bytes,
                pca_image_bytes=pca_image_bytes,
            )

        # AI interpretation for every cluster label that actually got written
        with SessionLocal() as session:
            labels = [r[0] for r in session.execute(
                text("SELECT cluster_label FROM cluster ORDER BY cluster_label")
            ).all()]
        print(f"  {version_tag}: {len(labels)} cluster rows written: {labels}")

        ai_ok = 0
        for label in labels:
            with SessionLocal() as session:
                svc = ClusterService(ClusterRepository(session))
                try:
                    svc.get_ai_analysis(label)
                    ai_ok += 1
                    print(f"    AI analysis done for cluster {label}")
                except Exception as e:
                    print(f"    [!] AI analysis FAILED for cluster {label}: {e}")
        print(f"  {version_tag}: AI analysis saved for {ai_ok}/{len(labels)} clusters")

        # export the fully-populated cluster table before the next run overwrites it
        with SessionLocal() as session:
            _export_cluster_table(
                session,
                dumps_dir / f"{version_tag}.json",
                version_tag,
                extra={
                    "run_tag": run_tag,
                    "preferred_k": k,
                    "n_clusters_written": len(labels),
                    "metrics": metrics_row,
                    "numerical": num_cols,
                    "categorical": cat_cols,
                },
            )

    print(f"\n{'=' * 70}\nDONE. DB now holds v55. JSON dumps in {dumps_dir}\n{'=' * 70}")


if __name__ == "__main__":
    main()
