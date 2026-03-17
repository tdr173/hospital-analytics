from sqlalchemy.orm import Session

from app.repository.statistics_repository.organization_repository import OrganizationRepository
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.provider_schema import UtilizationStats
from app.domain.schemas.statistics_schema.organization_schema import OrganizationStatisticsResponse


class OrganizationService:
    def __init__(self, db: Session):
        self.repo = OrganizationRepository(db)

    def get_organization_summary(self) -> OrganizationStatisticsResponse:
        utilization = self.repo.get_utilization_stats()

        return OrganizationStatisticsResponse(
            total_organizations=self.repo.get_total_organizations(),
            utilization=UtilizationStats(**utilization),
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
