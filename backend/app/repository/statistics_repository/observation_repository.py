from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from domain.models.observation_model import ObservationModel
from domain.models.patient_model import PatientModel


class ObservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_observations(self) -> int:
        return self.db.query(func.count(ObservationModel.observation_code)).scalar()

    def get_unique_observation_types(self) -> int:
        return self.db.query(func.count(func.distinct(ObservationModel.observation_code))).scalar()

    def get_top_observation_types(self, limit: int = 15):
        total = self.get_total_observations()

        rows = (
            self.db.query(
                ObservationModel.description.label("label"),
                func.count(ObservationModel.observation_code).label("count"),
            )
            .group_by(ObservationModel.description)
            .order_by(func.count(ObservationModel.observation_code).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_numeric_stats(self, limit: int = 25):
        total_patients = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                ObservationModel.description.label("label"),
                func.count(ObservationModel.observation_code).label("count"),
                func.count(func.distinct(ObservationModel.patient_id)).label("patient_count"),
                func.round(cast(func.min(ObservationModel.value_numeric), Numeric), 2).label("min_value"),
                func.round(cast(func.max(ObservationModel.value_numeric), Numeric), 2).label("max_value"),
                func.round(cast(func.avg(ObservationModel.value_numeric), Numeric), 2).label("avg_value"),
                ObservationModel.units,
            )
            .filter(ObservationModel.value_numeric.isnot(None))
            .group_by(ObservationModel.description, ObservationModel.units)
            .order_by(func.count(func.distinct(ObservationModel.patient_id)).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "label": row.label,
                "count": row.count,
                "patient_count": row.patient_count,
                "percentage": round(row.patient_count * 100.0 / total_patients, 2) if total_patients else 0,
                "min_value": float(row.min_value or 0),
                "max_value": float(row.max_value or 0),
                "avg_value": float(row.avg_value or 0),
                "units": row.units or "",
            }
            for row in rows
        ]

    def get_categorical_stats(self, limit: int = 15):
        total_patients = self.db.query(func.count(PatientModel.patient_id)).scalar()

        rows = (
            self.db.query(
                ObservationModel.description.label("label"),
                func.count(ObservationModel.observation_code).label("count"),
                func.count(func.distinct(ObservationModel.patient_id)).label("patient_count"),
                func.count(func.distinct(ObservationModel.value)).label("distinct_values"),
            )
            .filter(
                ObservationModel.value_numeric.is_(None),
                ObservationModel.value.isnot(None),
                ObservationModel.value != "",
            )
            .group_by(ObservationModel.description)
            .order_by(func.count(func.distinct(ObservationModel.patient_id)).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "label": row.label,
                "count": row.count,
                "patient_count": row.patient_count,
                "percentage": round(row.patient_count * 100.0 / total_patients, 2) if total_patients else 0,
                "distinct_values": row.distinct_values,
            }
            for row in rows
        ]

    def get_per_patient_stats(self):
        subquery = (
            self.db.query(
                ObservationModel.patient_id,
                func.count(ObservationModel.observation_code).label("cnt"),
            )
            .group_by(ObservationModel.patient_id)
            .subquery()
        )

        result = self.db.query(
            func.round(cast(func.avg(subquery.c.cnt), Numeric), 2).label("avg"),
            func.min(subquery.c.cnt).label("min"),
            func.max(subquery.c.cnt).label("max"),
        ).one()

        return {
            "avg": float(result.avg or 0),
            "min": result.min or 0,
            "max": result.max or 0,
        }

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
