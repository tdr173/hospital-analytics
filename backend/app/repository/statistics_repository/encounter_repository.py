from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from domain.models.encounter_model import EncounterModel
from repository.statistics_repository._common import compute_min_date, with_percentage


class EncounterRepository:
    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        min_date = compute_min_date(db, EncounterModel.start_date, range_str)
        self._filter = (
            EncounterModel.start_date >= min_date if min_date is not None else None
        )

    def _apply(self, q):
        return q.filter(self._filter) if self._filter is not None else q

    def get_total_encounters(self) -> int:
        return self._apply(self.db.query(func.count(EncounterModel.encounter_id))).scalar()

    def get_encounter_class_distribution(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_encounters()

        rows = self._apply(
            self.db.query(
                EncounterModel.encounter_class.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
        ).group_by(EncounterModel.encounter_class).order_by(
            func.count(EncounterModel.encounter_id).desc()
        ).all()
        return with_percentage(rows, total)

    def get_duration_stats_per_class(self):
        rows = self._apply(
            self.db.query(
                EncounterModel.encounter_class.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
                func.round(cast(func.min(EncounterModel.duration), Numeric), 2).label("min_duration"),
                func.round(cast(func.max(EncounterModel.duration), Numeric), 2).label("max_duration"),
                func.round(cast(func.avg(EncounterModel.duration), Numeric), 2).label("avg_duration"),
            )
        ).group_by(EncounterModel.encounter_class).order_by(
            func.count(EncounterModel.encounter_id).desc()
        ).all()
        return [
            {
                "label": row.label,
                "count": row.count,
                "min_duration": float(row.min_duration or 0),
                "max_duration": float(row.max_duration or 0),
                "avg_duration": float(row.avg_duration or 0),
            }
            for row in rows
        ]

    def get_top_descriptions(self, limit: int = 10, total: Optional[int] = None):
        if total is None:
            total = self.get_total_encounters()

        rows = self._apply(
            self.db.query(
                EncounterModel.description.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
        ).group_by(EncounterModel.description).order_by(
            func.count(EncounterModel.encounter_id).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_top_reason_descriptions(self, limit: int = 10):
        total_q = self.db.query(func.count(EncounterModel.encounter_id)).filter(
            EncounterModel.reason_description.isnot(None)
        )
        total = self._apply(total_q).scalar()

        rows = self._apply(
            self.db.query(
                EncounterModel.reason_description.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            ).filter(EncounterModel.reason_description.isnot(None))
        ).group_by(EncounterModel.reason_description).order_by(
            func.count(EncounterModel.encounter_id).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)
