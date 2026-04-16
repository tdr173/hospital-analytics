from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from repository.statistics_repository._common import with_percentage


class ObservationRepository:
    # Values come from mv_obs_* materialized views to avoid scanning millions of rows.

    def __init__(self, db: Session):
        self.db = db

    def get_total_observations(self) -> int:
        row = self.db.execute(text("SELECT total_observations FROM mv_obs_totals")).first()
        return int(row.total_observations) if row else 0

    def get_unique_observation_types(self) -> int:
        row = self.db.execute(text("SELECT unique_types FROM mv_obs_totals")).first()
        return int(row.unique_types) if row else 0

    def get_total_patients(self) -> int:
        row = self.db.execute(text("SELECT total_patients FROM mv_obs_totals")).first()
        return int(row.total_patients) if row else 0

    def get_per_patient_stats(self):
        row = self.db.execute(text(
            "SELECT avg_cnt, min_cnt, max_cnt FROM mv_obs_per_patient"
        )).first()
        if not row:
            return {"avg": 0, "min": 0, "max": 0}
        return {
            "avg": float(row.avg_cnt or 0),
            "min": row.min_cnt or 0,
            "max": row.max_cnt or 0,
        }

    def get_top_observation_types(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_observations()

        rows = self.db.execute(text(
            "SELECT description AS label, cnt AS count "
            "FROM mv_obs_top_types "
            "ORDER BY cnt DESC "
            "LIMIT :limit"
        ), {"limit": limit}).all()

        return with_percentage(rows, total)

    def get_numeric_stats(self, limit: int = 25, total_patients: Optional[int] = None):
        if total_patients is None:
            total_patients = self.get_total_patients()

        rows = self.db.execute(text(
            "SELECT description AS label, cnt AS count, patient_count, "
            "       min_val, max_val, avg_val, units "
            "FROM mv_obs_numeric_stats "
            "ORDER BY patient_count DESC "
            "LIMIT :limit"
        ), {"limit": limit}).all()

        return [
            {
                "label": row.label,
                "count": row.count,
                "patient_count": row.patient_count,
                "percentage": round(row.patient_count * 100.0 / total_patients, 2) if total_patients else 0,
                "min_value": float(row.min_val or 0),
                "max_value": float(row.max_val or 0),
                "avg_value": float(row.avg_val or 0),
                "units": row.units or "",
            }
            for row in rows
        ]

    def get_categorical_stats(self, limit: int = 15, total_patients: Optional[int] = None):
        if total_patients is None:
            total_patients = self.get_total_patients()

        rows = self.db.execute(text(
            "SELECT description AS label, cnt AS count, patient_count, distinct_values "
            "FROM mv_obs_categorical_stats "
            "ORDER BY patient_count DESC "
            "LIMIT :limit"
        ), {"limit": limit}).all()

        return [
            {
                "label": row.label,
                "count": row.count,
                "patient_count": row.patient_count,
                "percentage": round(row.patient_count * 100.0 / total_patients, 2) if total_patients else 0,
                "distinct_values": row.distinct_values,
            }
            for row in rows
        ]
