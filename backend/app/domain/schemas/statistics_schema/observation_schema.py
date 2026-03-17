from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats


class NumericStatsEntry(BaseModel):
    name: str
    count: int
    patient_count: int
    percentage: float
    min_value: float
    max_value: float
    avg_value: float
    units: str
    tooltip: str


class ObservationStatisticsResponse(BaseModel):
    total_observations: int
    unique_observation_types: int
    per_patient: PerPatientStats
    top_observation_types: list[ChartEntry]
    numeric_stats: list[NumericStatsEntry]
