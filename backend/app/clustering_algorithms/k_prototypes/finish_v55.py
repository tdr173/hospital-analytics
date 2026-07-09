"""Finish the interrupted run: complete v55 AI analysis + export v55.json.

v55 is already fully clustered and saved in the DB; only the last cluster's
ai_analysis and the JSON dump are missing. Cached clusters are returned without
an LLM call, so only the pending cluster actually hits the model.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/app

from dotenv import load_dotenv
from sqlalchemy import text


def main():
    load_dotenv()
    from db import SessionLocal
    from repository import ClusterRepository
    from service import ClusterService

    with SessionLocal() as session:
        labels = [r[0] for r in session.execute(
            text("SELECT cluster_label FROM cluster ORDER BY cluster_label")
        ).all()]
    print("v55 cluster labels:", labels)

    for label in labels:
        with SessionLocal() as session:
            svc = ClusterService(ClusterRepository(session))
            try:
                svc.get_ai_analysis(label)  # cached => no LLM call
                print(f"  AI analysis OK for cluster {label}")
            except Exception as e:
                print(f"  [!] AI analysis FAILED for cluster {label}: {e}")

    dumps_dir = Path(__file__).parent / "outputs" / "ai_dumps"
    dumps_dir.mkdir(parents=True, exist_ok=True)
    path = dumps_dir / "v55.json"

    with SessionLocal() as session:
        rows = session.execute(text(
            "SELECT id, cluster_label, color, title, description, insight, "
            "recommendation, ai_analysis, created_at FROM cluster ORDER BY cluster_label"
        )).mappings().all()
        meta = session.execute(text(
            "SELECT algorithm, n_clusters, n_patients, n_outliers, numerical_features, "
            "categorical_features, params, metrics, created_at FROM cluster_meta"
        )).mappings().first()

    payload = {
        "version": "v55",
        "run_tag": "v55_sminmax_gauto_rs42_th6_k4",
        "cluster_meta": dict(meta) if meta else None,
        "clusters": [dict(r) for r in rows],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    n_ai = sum(1 for r in rows if r["ai_analysis"] is not None)
    print(f"exported {len(rows)} clusters ({n_ai} with ai_analysis) -> {path}")


if __name__ == "__main__":
    main()
