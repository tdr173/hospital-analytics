from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from domain.models.immunization_model import ImmunizationModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, provider_patient_subq, with_percentage,
)


class ImmunizationRepository:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self._filters = []
        min_date = compute_min_date(db, ImmunizationModel.date, range_str)
        if min_date is not None:
            self._filters.append(ImmunizationModel.date >= min_date)
        if provider_id:
            subq = provider_patient_subq(db, provider_id)
            self._filters.append(ImmunizationModel.patient_id.in_(subq))

    def _apply(self, q):
        for f in self._filters:
            q = q.filter(f)
        return q

    def get_total_immunizations(self) -> int:
        return self._apply(
            self.db.query(func.count(ImmunizationModel.immunization_code))
        ).scalar()

    def get_unique_immunizations(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(ImmunizationModel.immunization_code)))
        ).scalar()

    def get_top_immunizations(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_immunizations()

        rows = self._apply(
            self.db.query(
                ImmunizationModel.description.label("label"),
                func.count(ImmunizationModel.immunization_code).label("count"),
            )
        ).group_by(ImmunizationModel.description).order_by(
            func.count(ImmunizationModel.immunization_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, ImmunizationModel, ImmunizationModel.immunization_code,
            filters=self._filters,
        )
