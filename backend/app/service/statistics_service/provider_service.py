from sqlalchemy.orm import Session

from app.repository.statistics_repository.provider_repository import ProviderRepository
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.provider_schema import (
    UtilizationStats,
    ProviderStatisticsResponse,
)


class ProviderService:
    def __init__(self, db: Session):
        self.repo = ProviderRepository(db)

    def get_provider_summary(self) -> ProviderStatisticsResponse:
        utilization = self.repo.get_utilization_stats()

        return ProviderStatisticsResponse(
            total_providers=self.repo.get_total_providers(),
            unique_specialities=self.repo.get_unique_specialities(),
            utilization=UtilizationStats(**utilization),
            gender=self._to_chart_entries(
                self.repo.get_gender_distribution(), "gender"
            ),
            top_specialities=self._to_chart_entries(
                self.repo.get_top_specialities(), "speciality"
            ),
            top_cities=self._to_chart_entries(
                self.repo.get_top_cities(), "city"
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
