from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class MedicationDurationStats(CamelModel):
    min_duration: float
    max_duration: float
    avg_duration: float
    median_duration: float


class MedicationStatisticsResponse(CamelModel):
    total_medications: int
    unique_medications: int
    per_patient: PerPatientStats
    duration_stats: MedicationDurationStats
    active_vs_ended: list[ChartEntry]
    top_medications: list[ChartEntry]
