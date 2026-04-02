from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.provider_schema import UtilizationStats


class OrganizationStatisticsResponse(CamelModel):
    total_organizations: int
    utilization: UtilizationStats
    top_cities: list[ChartEntry]
