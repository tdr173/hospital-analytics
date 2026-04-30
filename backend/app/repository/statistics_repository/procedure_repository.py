from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from domain.models.procedure_model import ProcedureModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, provider_patient_subq, with_percentage,
)


class ProcedureRepository:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self._filters = []
        min_date = compute_min_date(db, ProcedureModel.start_date, range_str)
        if min_date is not None:
            self._filters.append(ProcedureModel.start_date >= min_date)
        if provider_id:
            subq = provider_patient_subq(db, provider_id)
            self._filters.append(ProcedureModel.patient_id.in_(subq))

    def _apply(self, q):
        for f in self._filters:
            q = q.filter(f)
        return q

    def get_total_procedures(self) -> int:
        return self._apply(
            self.db.query(func.count(ProcedureModel.procedure_code))
        ).scalar()

    def get_unique_procedures(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(ProcedureModel.procedure_code)))
        ).scalar()

    def get_top_procedures(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_procedures()

        rows = self._apply(
            self.db.query(
                ProcedureModel.description.label("label"),
                func.count(ProcedureModel.procedure_code).label("count"),
            )
        ).group_by(ProcedureModel.description).order_by(
            func.count(ProcedureModel.procedure_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, ProcedureModel, ProcedureModel.procedure_code,
            filters=self._filters,
        )
