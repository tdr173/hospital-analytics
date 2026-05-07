from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from domain.models.careplan_model import CarePlanModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, with_percentage,
)


class CarePlanRepository:
    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        min_date = compute_min_date(db, CarePlanModel.start_date, range_str)
        self._filter = (
            CarePlanModel.start_date >= min_date if min_date is not None else None
        )

    def _apply(self, q):
        return q.filter(self._filter) if self._filter is not None else q

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
            filter_clause=self._filter,
        )
