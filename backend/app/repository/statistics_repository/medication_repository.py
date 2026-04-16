from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from domain.models.medication_model import MedicationModel
from repository.statistics_repository._common import with_percentage, per_patient_stats


class MedicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_medications(self) -> int:
        return self.db.query(func.count(MedicationModel.medication_code)).scalar()

    def get_unique_medications(self) -> int:
        return self.db.query(func.count(func.distinct(MedicationModel.medication_code))).scalar()

    def get_top_medications(self, limit: int = 20, total: Optional[int] = None):
        if total is None:
            total = self.get_total_medications()

        rows = (
            self.db.query(
                MedicationModel.description.label("label"),
                func.count(MedicationModel.medication_code).label("count"),
            )
            .group_by(MedicationModel.description)
            .order_by(func.count(MedicationModel.medication_code).desc())
            .limit(limit)
            .all()
        )
        return with_percentage(rows, total)

    def get_duration_stats(self):
        result = self.db.query(
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
        ).filter(
            MedicationModel.duration_days > 0
        ).one()

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

        rows = (
            self.db.query(
                status_label,
                func.count(MedicationModel.medication_code).label("count"),
            )
            .group_by(status_label)
            .all()
        )
        return with_percentage(rows, total)

    def get_per_patient_stats(self):
        return per_patient_stats(self.db, MedicationModel, MedicationModel.medication_code)
