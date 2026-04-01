from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from domain.models.condition_model import ConditionModel


class ConditionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_conditions(self) -> int:
        return self.db.query(func.count(ConditionModel.condition_code)).scalar()

    def get_unique_conditions(self) -> int:
        return self.db.query(func.count(func.distinct(ConditionModel.condition_code))).scalar()

    def get_active_vs_resolved(self):
        total = self.get_total_conditions()

        status_label = case(
            (ConditionModel.end_date.is_(None), "Active"),
            else_="Resolved",
        ).label("label")

        rows = (
            self.db.query(
                status_label,
                func.count(ConditionModel.condition_code).label("count"),
            )
            .group_by(status_label)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_top_conditions(self, limit: int = 20):
        total = self.get_total_conditions()

        rows = (
            self.db.query(
                ConditionModel.description.label("label"),
                func.count(ConditionModel.condition_code).label("count"),
            )
            .group_by(ConditionModel.description)
            .order_by(func.count(ConditionModel.condition_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                ConditionModel.patient_id,
                func.count(ConditionModel.condition_code).label("cnt"),
            )
            .group_by(ConditionModel.patient_id)
            .subquery()
        )

        result = self.db.query(
            func.round(cast(func.avg(subquery.c.cnt), Numeric), 2).label("avg"),
            func.min(subquery.c.cnt).label("min"),
            func.max(subquery.c.cnt).label("max"),
        ).one()

        return {
            "avg": float(result.avg or 0),
            "min": result.min or 0,
            "max": result.max or 0,
        }

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
