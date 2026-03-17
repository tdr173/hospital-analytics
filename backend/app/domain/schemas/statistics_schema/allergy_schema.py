from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats


class AllergyStatisticsResponse(BaseModel):
    total_allergies: int
    unique_allergies: int
    per_patient: PerPatientStats
    active_vs_resolved: list[ChartEntry]
    top_allergies: list[ChartEntry]
