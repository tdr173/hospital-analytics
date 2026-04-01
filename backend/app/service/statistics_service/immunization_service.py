from sqlalchemy.orm import Session

from repository.statistics_repository.immunization_repository import ImmunizationRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats
from domain.schemas.statistics_schemas.immunization_schema import ImmunizationStatisticsResponse


class ImmunizationService:
    def __init__(self, db: Session):
        self.repo = ImmunizationRepository(db)

    def get_immunization_summary(self) -> ImmunizationStatisticsResponse:
        per_patient = self.repo.get_per_patient_stats()

        return ImmunizationStatisticsResponse(
            total_immunizations=self.repo.get_total_immunizations(),
            unique_immunizations=self.repo.get_unique_immunizations(),
            per_patient=PerPatientStats(**per_patient),
            top_immunizations=self._to_chart_entries(
                self.repo.get_top_immunizations(), "immunization"
            ),
        )

    @staticmethod
    def _to_chart_entries(rows: list[dict], category: str) -> list[ChartEntry]:
        return [
            ChartEntry(
                name=row["label"] or "Unknown",
                value=row["count"],
                tooltip=f"{row['label'] or 'Unknown'}: {row['count']} ({row['percentage']}%)",
            )
            for row in rows
        ]
