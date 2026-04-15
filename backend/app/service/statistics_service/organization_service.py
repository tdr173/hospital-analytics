from sqlalchemy.orm import Session

from repository.statistics_repository.organization_repository import OrganizationRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.provider_schema import UtilizationStats
from domain.schemas.statistics_schemas.organization_schema import OrganizationStatisticsResponse


class OrganizationService:
    def __init__(self, db: Session):
        self.repo = OrganizationRepository(db)

    def get_organization_summary(self) -> OrganizationStatisticsResponse:
        total = self.repo.get_total_organizations()
        utilization = self.repo.get_utilization_stats()

        return OrganizationStatisticsResponse(
            total_organizations=total,
            utilization=UtilizationStats(**utilization),
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
