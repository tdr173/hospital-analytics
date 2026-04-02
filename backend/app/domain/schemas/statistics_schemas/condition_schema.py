from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry


class PerPatientStats(CamelModel):
    avg: float
    min: int
    max: int


class ConditionStatisticsResponse(CamelModel):
    total_conditions: int
    unique_conditions: int
    per_patient: PerPatientStats
    active_vs_resolved: list[ChartEntry]
    top_conditions: list[ChartEntry]
