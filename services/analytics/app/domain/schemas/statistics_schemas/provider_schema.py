from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry


class UtilizationStats(CamelModel):
    min: int
    max: int
    avg: float
    median: float


class ProviderStatisticsResponse(CamelModel):
    total_providers: int
    unique_specialities: int
    utilization: UtilizationStats
    gender: list[ChartEntry]
    top_specialities: list[ChartEntry]
    top_cities: list[ChartEntry]
