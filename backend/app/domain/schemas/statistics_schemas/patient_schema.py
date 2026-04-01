from pydantic import BaseModel


class ChartEntry(BaseModel):
    name: str
    value: float
    tooltip: str


class PatientStatisticsResponse(BaseModel):
    total_patients: int
    age_groups: list[ChartEntry]
    gender: list[ChartEntry]
    race: list[ChartEntry]
    ethnicity: list[ChartEntry]
    marital_status: list[ChartEntry]
    vital_status: list[ChartEntry]
    top_cities: list[ChartEntry]
