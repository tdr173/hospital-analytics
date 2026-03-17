from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats


class MedicationDurationStats(BaseModel):
    min_duration: float
    max_duration: float
    avg_duration: float
    median_duration: float


class MedicationStatisticsResponse(BaseModel):
    total_medications: int
    unique_medications: int
    per_patient: PerPatientStats
    duration_stats: MedicationDurationStats
    active_vs_ended: list[ChartEntry]
    top_medications: list[ChartEntry]
