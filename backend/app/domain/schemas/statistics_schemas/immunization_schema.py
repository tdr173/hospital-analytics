from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class ImmunizationStatisticsResponse(CamelModel):
    total_immunizations: int
    unique_immunizations: int
    per_patient: PerPatientStats
    top_immunizations: list[ChartEntry]
