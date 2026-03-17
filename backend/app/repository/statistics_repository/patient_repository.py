from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.domain.models.patient_model import PatientModel


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_patients(self) -> int:
        return self.db.query(func.count(PatientModel.patient_id)).scalar()

    def get_age_groups(self):
        age_group = case(
            (PatientModel.age.between(0, 18), "0-18"),
            (PatientModel.age.between(19, 35), "19-35"),
            (PatientModel.age.between(36, 50), "36-50"),
            (PatientModel.age.between(51, 65), "51-65"),
            else_="65+",
        ).label("label")

        total = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                age_group,
                func.count(PatientModel.patient_id).label("count"),
            )
            .group_by(age_group)
            .order_by(age_group)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_gender_distribution(self):
        return self._get_categorical_distribution(PatientModel.gender)

    def get_race_distribution(self):
        return self._get_categorical_distribution(PatientModel.race)

    def get_ethnicity_distribution(self):
        return self._get_categorical_distribution(PatientModel.ethnicity)

    def get_marital_status_distribution(self):
        return self._get_categorical_distribution(PatientModel.marital)

    def get_vital_status(self):
        vital_label = case(
            (PatientModel.deathdate.is_(None), "Alive"),
            else_="Deceased",
        ).label("label")

        total = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                vital_label,
                func.count(PatientModel.patient_id).label("count"),
            )
            .group_by(vital_label)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_top_cities(self):
        total = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                PatientModel.city.label("label"),
                func.count(PatientModel.patient_id).label("count"),
            )
            .group_by(PatientModel.city)
            .order_by(func.count(PatientModel.patient_id).desc())
            .all()
        )

        top_9 = rows[:9]
        others_count = sum(row.count for row in rows[9:])
        result = self._with_percentage(top_9, total)

        if others_count > 0:
            result.append({
                "label": "Others",
                "count": others_count,
                "percentage": round(others_count * 100.0 / total, 2) if total else 0,
            })

        return result

    def _get_categorical_distribution(self, column):
        total = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                column.label("label"),
                func.count(PatientModel.patient_id).label("count"),
            )
            .group_by(column)
            .order_by(func.count(PatientModel.patient_id).desc())
            .all()
        )
        return self._with_percentage(rows, total)

    @staticmethod
    def _with_percentage(rows, total):
        return [
            {
                "label": row.label,
                "count": row.count,
                "percentage": round(row.count * 100.0 / total, 2) if total else 0,
            }
            for row in rows
        ]
