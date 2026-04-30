from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from domain.models.careplan_model import CarePlanModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, provider_patient_subq, with_percentage,
)


class CarePlanRepository:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self._filters = []
        min_date = compute_min_date(db, CarePlanModel.start_date, range_str)
        if min_date is not None:
            self._filters.append(CarePlanModel.start_date >= min_date)
        if provider_id:
            subq = provider_patient_subq(db, provider_id)
            self._filters.append(CarePlanModel.patient_id.in_(subq))

    def _apply(self, q):
        for f in self._filters:
            q = q.filter(f)
        return q

    def get_total_careplans(self) -> int:
        return self._apply(
            self.db.query(func.count(CarePlanModel.careplan_code))
        ).scalar()

    def get_unique_careplans(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(CarePlanModel.careplan_code)))
        ).scalar()

    def get_top_careplans(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_careplans()

        rows = self._apply(
            self.db.query(
                CarePlanModel.description.label("label"),
                func.count(CarePlanModel.careplan_code).label("count"),
            )
        ).group_by(CarePlanModel.description).order_by(
            func.count(CarePlanModel.careplan_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_active_vs_ended(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_careplans()

        status_label = case(
            (CarePlanModel.end_date.is_(None), "Active"),
            else_="Ended",
        ).label("label")

        rows = self._apply(
            self.db.query(
                status_label,
                func.count(CarePlanModel.careplan_code).label("count"),
            )
        ).group_by(status_label).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, CarePlanModel, CarePlanModel.careplan_code,
            filters=self._filters,
        )
