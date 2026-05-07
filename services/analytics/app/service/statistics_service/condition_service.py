from sqlalchemy.orm import Session

from repository.statistics_repository.condition_repository import ConditionRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import (
    PerPatientStats,
    ConditionStatisticsResponse,
)


class ConditionService:
    def __init__(self, db: Session, range_str: str = "all"):
        self.repo = ConditionRepository(db, range_str)

    def get_condition_summary(self) -> ConditionStatisticsResponse:
        total = self.repo.get_total_conditions()
        per_patient = self.repo.get_per_patient_stats()

        return ConditionStatisticsResponse(
            total_conditions=total,
            unique_conditions=self.repo.get_unique_conditions(),
            per_patient=PerPatientStats(**per_patient),
            active_vs_resolved=self._to_chart_entries(
                self.repo.get_active_vs_resolved(total), "status"
            ),
            top_conditions=self._to_chart_entries(
                self.repo.get_top_conditions(total=total), "condition"
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
