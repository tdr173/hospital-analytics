from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from app.domain.models.encounter_model import EncounterModel


class EncounterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_encounters(self) -> int:
        return self.db.query(func.count(EncounterModel.encounter_id)).scalar()

    def get_encounter_class_distribution(self):
        total = self.get_total_encounters()

        rows = (
            self.db.query(
                EncounterModel.encounter_class.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
            .group_by(EncounterModel.encounter_class)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .all()
        )
        return self._with_percentage(rows, total)

    def get_duration_stats_per_class(self):
        rows = (
            self.db.query(
                EncounterModel.encounter_class.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
                func.round(cast(func.min(EncounterModel.duration), Numeric), 2).label("min_duration"),
                func.round(cast(func.max(EncounterModel.duration), Numeric), 2).label("max_duration"),
                func.round(cast(func.avg(EncounterModel.duration), Numeric), 2).label("avg_duration"),
            )
            .group_by(EncounterModel.encounter_class)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .all()
        )
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

    def get_top_descriptions(self, limit: int = 10):
        total = self.get_total_encounters()

        rows = (
            self.db.query(
                EncounterModel.description.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
            .group_by(EncounterModel.description)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_top_reason_descriptions(self, limit: int = 10):
        total = (
            self.db.query(func.count(EncounterModel.encounter_id))
            .filter(EncounterModel.reason_description.isnot(None))
            .scalar()
        )

        rows = (
            self.db.query(
                EncounterModel.reason_description.label("label"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
            .filter(EncounterModel.reason_description.isnot(None))
            .group_by(EncounterModel.reason_description)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    @staticmethod
    def _with_percentage(rows, total):
        return [
            {
                "label": row.label,
                "count": row.count,
                "percentage": round(row.count * 100.0 / total, 2) if total else 0,
            }
            for row in rows
        ]
