from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from repository.statistics_repository._common import compute_min_date, with_percentage
from domain.models.observation_model import ObservationModel


class ObservationRepository:
    """Observation is >1M rows. ``range=all`` reads from the pre-aggregated
    ``mv_obs_*`` materialized views for sub-second responses. ``week`` / ``month``
    fall back to direct aggregation against the ``observation`` table, filtered
    to the selected window; those queries are slower but still tractable since
    the window is small."""

    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        self.range_str = range_str
        self.min_date = compute_min_date(db, ObservationModel.date, range_str)

    # ---------------------------------------------------------------- totals

    def get_total_observations(self) -> int:
        if self.min_date is None:
            row = self.db.execute(text("SELECT total_observations FROM mv_obs_totals")).first()
            return int(row.total_observations) if row else 0
        row = self.db.execute(
            text("SELECT count(*) AS c FROM observation WHERE date >= :min_date"),
            {"min_date": self.min_date},
        ).first()
        return int(row.c) if row else 0

    def get_unique_observation_types(self) -> int:
        if self.min_date is None:
            row = self.db.execute(text("SELECT unique_types FROM mv_obs_totals")).first()
            return int(row.unique_types) if row else 0
        row = self.db.execute(
            text("SELECT count(DISTINCT observation_code) AS c FROM observation WHERE date >= :min_date"),
            {"min_date": self.min_date},
        ).first()
        return int(row.c) if row else 0

    def get_total_patients(self) -> int:
        if self.min_date is None:
            row = self.db.execute(text("SELECT total_patients FROM mv_obs_totals")).first()
            return int(row.total_patients) if row else 0
        row = self.db.execute(
            text("SELECT count(DISTINCT patient_id) AS c FROM observation WHERE date >= :min_date"),
            {"min_date": self.min_date},
        ).first()
        return int(row.c) if row else 0

    # ------------------------------------------------------- per-patient avg

    def get_per_patient_stats(self):
        if self.min_date is None:
            row = self.db.execute(text(
                "SELECT avg_cnt, min_cnt, max_cnt FROM mv_obs_per_patient"
            )).first()
        else:
            row = self.db.execute(
                text(
                    "SELECT round(cast(avg(cnt) AS numeric), 2) AS avg_cnt, "
                    "       min(cnt) AS min_cnt, "
                    "       max(cnt) AS max_cnt "
                    "FROM (SELECT patient_id, count(*) AS cnt "
                    "      FROM observation WHERE date >= :min_date "
                    "      GROUP BY patient_id) t"
                ),
                {"min_date": self.min_date},
            ).first()

        if not row:
            return {"avg": 0, "min": 0, "max": 0}
        return {
            "avg": float(row.avg_cnt or 0),
            "min": row.min_cnt or 0,
            "max": row.max_cnt or 0,
        }

    # ------------------------------------------------------------- top types

    def get_top_observation_types(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_observations()

        if self.min_date is None:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count "
                "FROM mv_obs_top_types ORDER BY cnt DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                "SELECT description AS label, count(*) AS count "
                "FROM observation WHERE date >= :min_date "
                "GROUP BY description ORDER BY count(*) DESC LIMIT :limit"
            ), {"limit": limit, "min_date": self.min_date}).all()

        return with_percentage(rows, total)

    # ---------------------------------------------------- numeric categories

    def get_numeric_stats(self, limit: int = 25, total_patients: Optional[int] = None):
        if total_patients is None:
            total_patients = self.get_total_patients()

        if self.min_date is None:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count, patient_count, "
                "       min_val, max_val, avg_val, units "
                "FROM mv_obs_numeric_stats ORDER BY patient_count DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                "SELECT description AS label, count(*) AS count, "
                "       count(DISTINCT patient_id) AS patient_count, "
                "       round(cast(min(value_numeric) AS numeric), 2) AS min_val, "
                "       round(cast(max(value_numeric) AS numeric), 2) AS max_val, "
                "       round(cast(avg(value_numeric) AS numeric), 2) AS avg_val, "
                "       units "
                "FROM observation "
                "WHERE value_numeric IS NOT NULL AND date >= :min_date "
                "GROUP BY description, units "
                "ORDER BY count(DISTINCT patient_id) DESC LIMIT :limit"
            ), {"limit": limit, "min_date": self.min_date}).all()

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

        if self.min_date is None:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count, patient_count, distinct_values "
                "FROM mv_obs_categorical_stats ORDER BY patient_count DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                "SELECT description AS label, count(*) AS count, "
                "       count(DISTINCT patient_id) AS patient_count, "
                "       count(DISTINCT value) AS distinct_values "
                "FROM observation "
                "WHERE value_numeric IS NULL AND value IS NOT NULL AND value != '' "
                "  AND date >= :min_date "
                "GROUP BY description "
                "ORDER BY count(DISTINCT patient_id) DESC LIMIT :limit"
            ), {"limit": limit, "min_date": self.min_date}).all()

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
