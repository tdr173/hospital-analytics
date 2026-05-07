from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.db_connector import get_clinical_db as get_db
from .statistics_router import statistics_router

_VIEWS = [
    "mv_obs_totals",
    "mv_obs_per_patient",
    "mv_obs_top_types",
    "mv_obs_numeric_stats",
    "mv_obs_categorical_stats",
]


@statistics_router.post("/observations/refresh")
def refresh_observation_views(db: Session = Depends(get_db)):
    """Rebuild observation materialized views after an ETL reload."""
    for view in _VIEWS:
        db.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
    db.commit()
    return {"status": "ok", "refreshed": _VIEWS}
