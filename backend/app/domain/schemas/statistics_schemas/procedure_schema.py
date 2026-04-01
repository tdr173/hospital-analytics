from pydantic import BaseModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class ProcedureStatisticsResponse(BaseModel):
    total_procedures: int
    unique_procedures: int
    per_patient: PerPatientStats
    top_procedures: list[ChartEntry]
