from sqlalchemy.orm import Session

from repository.statistics_repository.careplan_repository import CarePlanRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats
from domain.schemas.statistics_schemas.careplan_schema import CarePlanStatisticsResponse


class CarePlanService:
    def __init__(self, db: Session):
        self.repo = CarePlanRepository(db)

    def get_careplan_summary(self) -> CarePlanStatisticsResponse:
        total = self.repo.get_total_careplans()
        per_patient = self.repo.get_per_patient_stats()

        return CarePlanStatisticsResponse(
            total_careplans=total,
            unique_careplans=self.repo.get_unique_careplans(),
            per_patient=PerPatientStats(**per_patient),
            active_vs_ended=self._to_chart_entries(
                self.repo.get_active_vs_ended(total), "status"
            ),
            top_careplans=self._to_chart_entries(
                self.repo.get_top_careplans(total=total), "careplan"
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
