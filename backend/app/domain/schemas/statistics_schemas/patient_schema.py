from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel


class ChartEntry(CamelModel):
    name: str
    value: float
    tooltip: str


class PatientStatisticsResponse(CamelModel):
    total_patients: int
    age_groups: list[ChartEntry]
    gender: list[ChartEntry]
    race: list[ChartEntry]
    ethnicity: list[ChartEntry]
    marital_status: list[ChartEntry]
    vital_status: list[ChartEntry]
    top_cities: list[ChartEntry]
