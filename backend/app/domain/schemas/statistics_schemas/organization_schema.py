from pydantic import BaseModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.provider_schema import UtilizationStats


class OrganizationStatisticsResponse(BaseModel):
    total_organizations: int
    utilization: UtilizationStats
    top_cities: list[ChartEntry]
