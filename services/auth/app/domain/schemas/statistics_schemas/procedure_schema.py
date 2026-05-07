from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class ProcedureStatisticsResponse(CamelModel):
    total_procedures: int
    unique_procedures: int
    per_patient: PerPatientStats
    top_procedures: list[ChartEntry]
