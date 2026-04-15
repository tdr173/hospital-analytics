from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from domain.models.careplan_model import CarePlanModel


class CarePlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_careplans(self) -> int:
        return self.db.query(func.count(CarePlanModel.careplan_code)).scalar()

    def get_unique_careplans(self) -> int:
        return self.db.query(func.count(func.distinct(CarePlanModel.careplan_code))).scalar()

    def get_top_careplans(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_careplans()

        rows = (
            self.db.query(
                CarePlanModel.description.label("label"),
                func.count(CarePlanModel.careplan_code).label("count"),
            )
            .group_by(CarePlanModel.description)
            .order_by(func.count(CarePlanModel.careplan_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_active_vs_ended(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_careplans()

        status_label = case(
            (CarePlanModel.end_date.is_(None), "Active"),
            else_="Ended",
        ).label("label")

        rows = (
            self.db.query(
                status_label,
                func.count(CarePlanModel.careplan_code).label("count"),
            )
            .group_by(status_label)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                CarePlanModel.patient_id,
                func.count(CarePlanModel.careplan_code).label("cnt"),
            )
            .group_by(CarePlanModel.patient_id)
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
