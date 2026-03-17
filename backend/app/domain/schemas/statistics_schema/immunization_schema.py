from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats


class ImmunizationStatisticsResponse(BaseModel):
    total_immunizations: int
    unique_immunizations: int
    per_patient: PerPatientStats
    top_immunizations: list[ChartEntry]
