from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from domain.models.medication_model import MedicationModel
from repository.statistics_repository._common import (
    compute_min_date, per_patient_stats, with_percentage,
)


class MedicationRepository:
    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        min_date = compute_min_date(db, MedicationModel.start_date, range_str)
        self._filter = (
            MedicationModel.start_date >= min_date if min_date is not None else None
        )

    def _apply(self, q):
        return q.filter(self._filter) if self._filter is not None else q

    def get_total_medications(self) -> int:
        return self._apply(
            self.db.query(func.count(MedicationModel.medication_code))
        ).scalar()

    def get_unique_medications(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(MedicationModel.medication_code)))
        ).scalar()

    def get_top_medications(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_medications()

        rows = self._apply(
            self.db.query(
                MedicationModel.description.label("label"),
                func.count(MedicationModel.medication_code).label("count"),
            )
        ).group_by(MedicationModel.description).order_by(
            func.count(MedicationModel.medication_code).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_duration_stats(self):
        q = self.db.query(
            func.round(cast(func.min(MedicationModel.duration_days), Numeric), 2).label("min_duration"),
            func.round(cast(func.max(MedicationModel.duration_days), Numeric), 2).label("max_duration"),
            func.round(cast(func.avg(MedicationModel.duration_days), Numeric), 2).label("avg_duration"),
            func.round(
                cast(
                    func.percentile_cont(0.5).within_group(MedicationModel.duration_days),
                    Numeric,
                ),
                2,
            ).label("median_duration"),
        ).filter(MedicationModel.duration_days > 0)

        result = self._apply(q).one()

        return {
            "min_duration": float(result.min_duration or 0),
            "max_duration": float(result.max_duration or 0),
            "avg_duration": float(result.avg_duration or 0),
            "median_duration": float(result.median_duration or 0),
        }

    def get_active_vs_ended(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_medications()

        status_label = case(
            (MedicationModel.end_date.is_(None), "Active"),
            else_="Ended",
        ).label("label")

        rows = self._apply(
            self.db.query(
                status_label,
                func.count(MedicationModel.medication_code).label("count"),
            )
        ).group_by(status_label).all()
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(
            self.db, MedicationModel, MedicationModel.medication_code,
            filter_clause=self._filter,
        )
