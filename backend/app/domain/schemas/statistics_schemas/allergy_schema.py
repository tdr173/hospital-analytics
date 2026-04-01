from pydantic import BaseModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class AllergyStatisticsResponse(BaseModel):
    total_allergies: int
    unique_allergies: int
    per_patient: PerPatientStats
    active_vs_resolved: list[ChartEntry]
    top_allergies: list[ChartEntry]
