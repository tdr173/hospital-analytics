from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats


class ProcedureStatisticsResponse(BaseModel):
    total_procedures: int
    unique_procedures: int
    per_patient: PerPatientStats
    top_procedures: list[ChartEntry]
