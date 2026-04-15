from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from domain.models.allergy_model import AllergyModel


class AllergyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_allergies(self) -> int:
        return self.db.query(func.count(AllergyModel.allergy_code)).scalar()

    def get_unique_allergies(self) -> int:
        return self.db.query(func.count(func.distinct(AllergyModel.allergy_code))).scalar()

    def get_top_allergies(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_allergies()

        rows = (
            self.db.query(
                AllergyModel.description.label("label"),
                func.count(AllergyModel.allergy_code).label("count"),
            )
            .group_by(AllergyModel.description)
            .order_by(func.count(AllergyModel.allergy_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_active_vs_resolved(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_allergies()

        status_label = case(
            (AllergyModel.end_date.is_(None), "Active"),
            else_="Resolved",
        ).label("label")

        rows = (
            self.db.query(
                status_label,
                func.count(AllergyModel.allergy_code).label("count"),
            )
            .group_by(status_label)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                AllergyModel.patient_id,
                func.count(AllergyModel.allergy_code).label("cnt"),
            )
            .group_by(AllergyModel.patient_id)
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
