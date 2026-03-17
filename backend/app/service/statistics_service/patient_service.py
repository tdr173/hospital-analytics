from sqlalchemy.orm import Session

from app.repository.statistics_repository.patient_repository import PatientRepository
from app.domain.schemas.statistics_schema.patient_schema import (
    ChartEntry,
    PatientStatisticsResponse,
)


class PatientService:
    def __init__(self, db: Session):
        self.repo = PatientRepository(db)

    def get_patient_summary(self) -> PatientStatisticsResponse:
        total = self.repo.get_total_patients()

        return PatientStatisticsResponse(
            total_patients=total,
            age_groups=self._to_chart_entries(self.repo.get_age_groups(), "age group"),
            gender=self._to_chart_entries(self.repo.get_gender_distribution(), "gender"),
            race=self._to_chart_entries(self.repo.get_race_distribution(), "race"),
            ethnicity=self._to_chart_entries(self.repo.get_ethnicity_distribution(), "ethnicity"),
            marital_status=self._to_chart_entries(self.repo.get_marital_status_distribution(), "marital status"),
            vital_status=self._to_chart_entries(self.repo.get_vital_status(), "vital status"),
            top_cities=self._to_chart_entries(self.repo.get_top_cities(), "city"),
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
