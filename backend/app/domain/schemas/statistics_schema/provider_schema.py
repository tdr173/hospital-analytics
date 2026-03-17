from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry


class UtilizationStats(BaseModel):
    min: int
    max: int
    avg: float
    median: float


class ProviderStatisticsResponse(BaseModel):
    total_providers: int
    unique_specialities: int
    utilization: UtilizationStats
    gender: list[ChartEntry]
    top_specialities: list[ChartEntry]
    top_cities: list[ChartEntry]
