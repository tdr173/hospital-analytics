from sqlalchemy.orm import Session

from repository.statistics_repository.provider_repository import ProviderRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.provider_schema import (
    UtilizationStats,
    ProviderStatisticsResponse,
)


class ProviderService:
    def __init__(self, db: Session, range_str: str = "all"):
        self.repo = ProviderRepository(db, range_str)

    def get_provider_summary(self) -> ProviderStatisticsResponse:
        total = self.repo.get_total_providers()
        utilization = self.repo.get_utilization_stats()

        return ProviderStatisticsResponse(
            total_providers=total,
            unique_specialities=self.repo.get_unique_specialities(),
            utilization=UtilizationStats(**utilization),
            gender=self._to_chart_entries(
                self.repo.get_gender_distribution(total), "gender"
            ),
            top_specialities=self._to_chart_entries(
                self.repo.get_top_specialities(total=total), "speciality"
            ),
            top_cities=self._to_chart_entries(
                self.repo.get_top_cities(total=total), "city"
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
