from sqlalchemy.orm import Session

from app.repository.statistics_repository.allergy_repository import AllergyRepository
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats
from app.domain.schemas.statistics_schema.allergy_schema import AllergyStatisticsResponse


class AllergyService:
    def __init__(self, db: Session):
        self.repo = AllergyRepository(db)

    def get_allergy_summary(self) -> AllergyStatisticsResponse:
        per_patient = self.repo.get_per_patient_stats()

        return AllergyStatisticsResponse(
            total_allergies=self.repo.get_total_allergies(),
            unique_allergies=self.repo.get_unique_allergies(),
            per_patient=PerPatientStats(**per_patient),
            active_vs_resolved=self._to_chart_entries(
                self.repo.get_active_vs_resolved(), "status"
            ),
            top_allergies=self._to_chart_entries(
                self.repo.get_top_allergies(), "allergy"
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
