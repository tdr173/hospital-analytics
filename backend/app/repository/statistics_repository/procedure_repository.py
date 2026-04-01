from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from domain.models.procedure_model import ProcedureModel


class ProcedureRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_procedures(self) -> int:
        return self.db.query(func.count(ProcedureModel.procedure_code)).scalar()

    def get_unique_procedures(self) -> int:
        return self.db.query(func.count(func.distinct(ProcedureModel.procedure_code))).scalar()

    def get_top_procedures(self, limit: int = 20):
        total = self.get_total_procedures()

        rows = (
            self.db.query(
                ProcedureModel.description.label("label"),
                func.count(ProcedureModel.procedure_code).label("count"),
            )
            .group_by(ProcedureModel.description)
            .order_by(func.count(ProcedureModel.procedure_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                ProcedureModel.patient_id,
                func.count(ProcedureModel.procedure_code).label("cnt"),
            )
            .group_by(ProcedureModel.patient_id)
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
