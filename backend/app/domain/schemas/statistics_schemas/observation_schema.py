from pydantic import BaseModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


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


class CategoricalStatsEntry(BaseModel):
    name: str
    count: int
    patient_count: int
    percentage: float
    distinct_values: int
    tooltip: str


class ObservationStatisticsResponse(BaseModel):
    total_observations: int
    unique_observation_types: int
    per_patient: PerPatientStats
    top_observation_types: list[ChartEntry]
    numeric_stats: list[NumericStatsEntry]
    categorical_stats: list[CategoricalStatsEntry]
