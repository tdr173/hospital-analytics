from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from domain.models.patient_model import PatientModel
from domain.models.encounter_model import EncounterModel
from repository.statistics_repository._common import (
    compute_min_date, with_percentage,
)


class PatientRepository:
    def __init__(self, db: Session, range_str: str = "all"):
        self.db = db
        # Patients have no intrinsic date column - range filters down to the set
        # of patients who had encounters within the window.
        min_date = compute_min_date(db, EncounterModel.start_date, range_str)
        if min_date is not None:
            active_ids = (
                db.query(EncounterModel.patient_id)
                .filter(EncounterModel.start_date >= min_date)
                .distinct()
                .subquery()
            )
            self._filter = PatientModel.patient_id.in_(active_ids)
        else:
            self._filter = None

    def _apply(self, q):
        return q.filter(self._filter) if self._filter is not None else q

    def get_total_patients(self) -> int:
        return self._apply(
            self.db.query(func.count(PatientModel.patient_id))
        ).scalar()

    def get_age_groups(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_patients()

        age_group = case(
            (PatientModel.age.between(0, 18), "0-18"),
            (PatientModel.age.between(19, 35), "19-35"),
            (PatientModel.age.between(36, 50), "36-50"),
            (PatientModel.age.between(51, 65), "51-65"),
            else_="65+",
        ).label("label")

        rows = self._apply(
            self.db.query(
                age_group,
                func.count(PatientModel.patient_id).label("count"),
            )
        ).group_by(age_group).order_by(age_group).all()
        return with_percentage(rows, total)

    def get_gender_distribution(self, total: Optional[int] = None):
        return self._categorical_distribution(PatientModel.gender, total)

    def get_race_distribution(self, total: Optional[int] = None):
        return self._categorical_distribution(PatientModel.race, total)

    def get_ethnicity_distribution(self, total: Optional[int] = None):
        return self._categorical_distribution(PatientModel.ethnicity, total)

    def get_marital_status_distribution(self, total: Optional[int] = None):
        return self._categorical_distribution(PatientModel.marital, total)

    def get_vital_status(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_patients()

        vital_label = case(
            (PatientModel.deathdate.is_(None), "Alive"),
            else_="Deceased",
        ).label("label")

        rows = self._apply(
            self.db.query(
                vital_label,
                func.count(PatientModel.patient_id).label("count"),
            )
        ).group_by(vital_label).all()
        return with_percentage(rows, total)

    def get_top_cities(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_patients()

        rows = self._apply(
            self.db.query(
                PatientModel.city.label("label"),
                func.count(PatientModel.patient_id).label("count"),
            )
        ).group_by(PatientModel.city).order_by(
            func.count(PatientModel.patient_id).desc()
        ).all()

        top_9 = rows[:9]
        others_count = sum(row.count for row in rows[9:])
        result = with_percentage(top_9, total)

        if others_count > 0:
            result.append({
                "label": "Others",
                "count": others_count,
                "percentage": round(others_count * 100.0 / total, 2) if total else 0,
            })

        return result

    def _categorical_distribution(self, column, total: Optional[int] = None):
        if total is None:
            total = self.get_total_patients()

        rows = self._apply(
            self.db.query(
                column.label("label"),
                func.count(PatientModel.patient_id).label("count"),
            )
        ).group_by(column).order_by(
            func.count(PatientModel.patient_id).desc()
        ).all()
        return with_percentage(rows, total)
