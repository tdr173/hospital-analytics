from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.provider_schema import UtilizationStats


class OrganizationStatisticsResponse(BaseModel):
    total_organizations: int
    utilization: UtilizationStats
    top_cities: list[ChartEntry]
