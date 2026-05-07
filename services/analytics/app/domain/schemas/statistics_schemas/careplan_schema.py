from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats


class CarePlanStatisticsResponse(CamelModel):
    total_careplans: int
    unique_careplans: int
    per_patient: PerPatientStats
    active_vs_ended: list[ChartEntry]
    top_careplans: list[ChartEntry]
