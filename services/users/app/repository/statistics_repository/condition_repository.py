from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from domain.models.condition_model import ConditionModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, with_percentage,
)


class ConditionRepository:
    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        min_date = compute_min_date(db, ConditionModel.start_date, range_str)
        self._filter = (
            ConditionModel.start_date >= min_date if min_date is not None else None
        )

    def _apply(self, q):
        return q.filter(self._filter) if self._filter is not None else q

    def get_total_conditions(self) -> int:
        return self._apply(
            self.db.query(func.count(ConditionModel.condition_code))
        ).scalar()

    def get_unique_conditions(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(ConditionModel.condition_code)))
        ).scalar()

    def get_active_vs_resolved(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_conditions()

        status_label = case(
            (ConditionModel.end_date.is_(None), "Active"),
            else_="Resolved",
        ).label("label")

        rows = self._apply(
            self.db.query(
                status_label,
                func.count(ConditionModel.condition_code).label("count"),
            )
        ).group_by(status_label).all()
        return with_percentage(rows, total)

    def get_top_conditions(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_conditions()

        rows = self._apply(
            self.db.query(
                ConditionModel.description.label("label"),
                func.count(ConditionModel.condition_code).label("count"),
            )
        ).group_by(ConditionModel.description).order_by(
            func.count(ConditionModel.condition_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, ConditionModel, ConditionModel.condition_code,
            filter_clause=self._filter,
        )
