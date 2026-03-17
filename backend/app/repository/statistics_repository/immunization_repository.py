from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from app.domain.models.immunization_model import ImmunizationModel


class ImmunizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_immunizations(self) -> int:
        return self.db.query(func.count(ImmunizationModel.immunization_code)).scalar()

    def get_unique_immunizations(self) -> int:
        return self.db.query(func.count(func.distinct(ImmunizationModel.immunization_code))).scalar()

    def get_top_immunizations(self, limit: int = 15):
        total = self.get_total_immunizations()

        rows = (
            self.db.query(
                ImmunizationModel.description.label("label"),
                func.count(ImmunizationModel.immunization_code).label("count"),
            )
            .group_by(ImmunizationModel.description)
            .order_by(func.count(ImmunizationModel.immunization_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                ImmunizationModel.patient_id,
                func.count(ImmunizationModel.immunization_code).label("cnt"),
            )
            .group_by(ImmunizationModel.patient_id)
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
