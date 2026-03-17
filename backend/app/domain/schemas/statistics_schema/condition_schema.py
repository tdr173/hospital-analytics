from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry


class PerPatientStats(BaseModel):
    avg: float
    min: int
    max: int


class ConditionStatisticsResponse(BaseModel):
    total_conditions: int
    unique_conditions: int
    per_patient: PerPatientStats
    active_vs_resolved: list[ChartEntry]
    top_conditions: list[ChartEntry]
