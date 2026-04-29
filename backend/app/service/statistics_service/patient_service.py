from sqlalchemy.orm import Session

from repository.statistics_repository.patient_repository import PatientRepository
from domain.schemas.statistics_schemas.patient_schema import (
    ChartEntry,
    PatientStatisticsResponse,
)


class PatientService:
    def __init__(self, db: Session, range_str: str = "all"):
        self.repo = PatientRepository(db, range_str)

    def get_patient_summary(self) -> PatientStatisticsResponse:
        total = self.repo.get_total_patients()

        return PatientStatisticsResponse(
            total_patients=total,
            age_groups=self._to_chart_entries(self.repo.get_age_groups(total), "age group"),
            gender=self._to_chart_entries(self.repo.get_gender_distribution(total), "gender"),
            race=self._to_chart_entries(self.repo.get_race_distribution(total), "race"),
            ethnicity=self._to_chart_entries(self.repo.get_ethnicity_distribution(total), "ethnicity"),
            marital_status=self._to_chart_entries(self.repo.get_marital_status_distribution(total), "marital status"),
            vital_status=self._to_chart_entries(self.repo.get_vital_status(total), "vital status"),
            top_cities=self._to_chart_entries(self.repo.get_top_cities(total), "city"),
        )

    @staticmethod
    def _to_chart_entries(rows: list[dict], category: str) -> list[ChartEntry]:
        return [
            ChartEntry(
                name=row["label"] or "Unknown",
                value=row["count"],
                tooltip=f"{row['label'] or 'Unknown'}: {row['count']} patients ({row['percentage']}%)",
            )
            for row in rows
        ]
