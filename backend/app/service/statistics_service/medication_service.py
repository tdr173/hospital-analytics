from typing import Optional
from sqlalchemy.orm import Session

from repository.statistics_repository.medication_repository import MedicationRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats
from domain.schemas.statistics_schemas.medication_schema import (
    MedicationDurationStats,
    MedicationStatisticsResponse,
)


class MedicationService:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.repo = MedicationRepository(db, range_str, provider_id)

    def get_medication_summary(self) -> MedicationStatisticsResponse:
        total = self.repo.get_total_medications()
        per_patient = self.repo.get_per_patient_stats()
        duration = self.repo.get_duration_stats()

        return MedicationStatisticsResponse(
            total_medications=total,
            unique_medications=self.repo.get_unique_medications(),
            per_patient=PerPatientStats(**per_patient),
            duration_stats=MedicationDurationStats(**duration),
            active_vs_ended=self._to_chart_entries(
                self.repo.get_active_vs_ended(total), "status"
            ),
            top_medications=self._to_chart_entries(
                self.repo.get_top_medications(total=total), "medication"
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
