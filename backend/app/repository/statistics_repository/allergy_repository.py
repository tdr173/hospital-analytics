from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from domain.models.allergy_model import AllergyModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, provider_patient_subq, with_percentage,
)


class AllergyRepository:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self._filters = []
        min_date = compute_min_date(db, AllergyModel.start_date, range_str)
        if min_date is not None:
            self._filters.append(AllergyModel.start_date >= min_date)
        if provider_id:
            subq = provider_patient_subq(db, provider_id)
            self._filters.append(AllergyModel.patient_id.in_(subq))

    def _apply(self, q):
        for f in self._filters:
            q = q.filter(f)
        return q

    def get_total_allergies(self) -> int:
        return self._apply(
            self.db.query(func.count(AllergyModel.allergy_code))
        ).scalar()

    def get_unique_allergies(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(AllergyModel.allergy_code)))
        ).scalar()

    def get_top_allergies(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_allergies()

        rows = self._apply(
            self.db.query(
                AllergyModel.description.label("label"),
                func.count(AllergyModel.allergy_code).label("count"),
            )
        ).group_by(AllergyModel.description).order_by(
            func.count(AllergyModel.allergy_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_active_vs_resolved(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_allergies()

        status_label = case(
            (AllergyModel.end_date.is_(None), "Active"),
            else_="Resolved",
        ).label("label")

        rows = self._apply(
            self.db.query(
                status_label,
                func.count(AllergyModel.allergy_code).label("count"),
            )
        ).group_by(status_label).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, AllergyModel, AllergyModel.allergy_code,
            filters=self._filters,
        )
