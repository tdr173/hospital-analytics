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
    the window is small. When ``provider_id`` is set the materialized views are
    bypassed because they contain all patients."""

    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self.range_str = range_str
        self.provider_id = provider_id
        self.min_date = compute_min_date(db, ObservationModel.date, range_str)
        # When filtering by provider we always use direct queries
        self._use_views = self.min_date is None and provider_id is None

    def _patient_clause(self) -> str:
        if self.provider_id:
            return (
                "patient_id IN "
                "(SELECT DISTINCT patient_id FROM encounter WHERE provider_id = :provider_id)"
            )
        return ""

    def _where(self, *extra: str) -> str:
        parts = [p for p in extra if p]
        if self.min_date is not None:
            parts.append("date >= :min_date")
        pat = self._patient_clause()
        if pat:
            parts.append(pat)
        return ("WHERE " + " AND ".join(parts)) if parts else ""

    def _params(self, **extra) -> dict:
        p = dict(extra)
        if self.min_date is not None:
            p["min_date"] = self.min_date
        if self.provider_id:
            p["provider_id"] = self.provider_id
        return p

    # ---------------------------------------------------------------- totals

    def get_total_observations(self) -> int:
        if self._use_views:
            row = self.db.execute(text("SELECT total_observations FROM mv_obs_totals")).first()
            return int(row.total_observations) if row else 0
        row = self.db.execute(
            text(f"SELECT count(*) AS c FROM observation {self._where()}"),
            self._params(),
        ).first()
        return int(row.c) if row else 0

    def get_unique_observation_types(self) -> int:
        if self._use_views:
            row = self.db.execute(text("SELECT unique_types FROM mv_obs_totals")).first()
            return int(row.unique_types) if row else 0
        row = self.db.execute(
            text(f"SELECT count(DISTINCT observation_code) AS c FROM observation {self._where()}"),
            self._params(),
        ).first()
        return int(row.c) if row else 0

    def get_total_patients(self) -> int:
        if self._use_views:
            row = self.db.execute(text("SELECT total_patients FROM mv_obs_totals")).first()
            return int(row.total_patients) if row else 0
        row = self.db.execute(
            text(f"SELECT count(DISTINCT patient_id) AS c FROM observation {self._where()}"),
            self._params(),
        ).first()
        return int(row.c) if row else 0

    # ------------------------------------------------------- per-patient avg

    def get_per_patient_stats(self):
        if self._use_views:
            row = self.db.execute(text(
                "SELECT avg_cnt, min_cnt, max_cnt FROM mv_obs_per_patient"
            )).first()
        else:
            row = self.db.execute(
                text(
                    "SELECT round(cast(avg(cnt) AS numeric), 2) AS avg_cnt, "
                    "       min(cnt) AS min_cnt, "
                    "       max(cnt) AS max_cnt "
                    f"FROM (SELECT patient_id, count(*) AS cnt "
                    f"      FROM observation {self._where()} "
                    f"      GROUP BY patient_id) t"
                ),
                self._params(),
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

        if self._use_views:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count "
                "FROM mv_obs_top_types ORDER BY cnt DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                f"SELECT description AS label, count(*) AS count "
                f"FROM observation {self._where()} "
                f"GROUP BY description ORDER BY count(*) DESC LIMIT :limit"
            ), self._params(limit=limit)).all()

        return with_percentage(rows, total)

    # ---------------------------------------------------- numeric categories

    def get_numeric_stats(self, limit: int = 25, total_patients: Optional[int] = None):
        if total_patients is None:
            total_patients = self.get_total_patients()

        if self._use_views:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count, patient_count, "
                "       min_val, max_val, avg_val, units "
                "FROM mv_obs_numeric_stats ORDER BY patient_count DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                f"SELECT description AS label, count(*) AS count, "
                f"       count(DISTINCT patient_id) AS patient_count, "
                f"       round(cast(min(value_numeric) AS numeric), 2) AS min_val, "
                f"       round(cast(max(value_numeric) AS numeric), 2) AS max_val, "
                f"       round(cast(avg(value_numeric) AS numeric), 2) AS avg_val, "
                f"       units "
                f"FROM observation "
                f"{self._where('value_numeric IS NOT NULL')} "
                f"GROUP BY description, units "
                f"ORDER BY count(DISTINCT patient_id) DESC LIMIT :limit"
            ), self._params(limit=limit)).all()

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

        if self._use_views:
            rows = self.db.execute(text(
                "SELECT description AS label, cnt AS count, patient_count, distinct_values "
                "FROM mv_obs_categorical_stats ORDER BY patient_count DESC LIMIT :limit"
            ), {"limit": limit}).all()
        else:
            rows = self.db.execute(text(
                f"SELECT description AS label, count(*) AS count, "
                f"       count(DISTINCT patient_id) AS patient_count, "
                f"       count(DISTINCT value) AS distinct_values "
                f"FROM observation "
                f"{self._where('value_numeric IS NULL', 'value IS NOT NULL', \"value != ''\")} "
                f"GROUP BY description "
                f"ORDER BY count(DISTINCT patient_id) DESC LIMIT :limit"
            ), self._params(limit=limit)).all()

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
