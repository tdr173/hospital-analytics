from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from domain.models.procedure_model import ProcedureModel
from repository.statistics_repository._common import with_percentage, per_patient_stats


class ProcedureRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_procedures(self) -> int:
        return self.db.query(func.count(ProcedureModel.procedure_code)).scalar()

    def get_unique_procedures(self) -> int:
        return self.db.query(func.count(func.distinct(ProcedureModel.procedure_code))).scalar()

    def get_top_procedures(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
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
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(self.db, ProcedureModel, ProcedureModel.procedure_code)
