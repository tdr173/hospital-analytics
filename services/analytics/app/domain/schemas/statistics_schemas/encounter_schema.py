from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel
from domain.schemas.statistics_schemas.patient_schema import ChartEntry


class DurationStatsEntry(CamelModel):
    name: str
    count: int
    min_duration: float
    max_duration: float
    avg_duration: float
    median_duration: float
    tooltip: str


class EncounterStatisticsResponse(CamelModel):
    total_encounters: int
    encounter_class: list[ChartEntry]
    duration_stats: list[DurationStatsEntry]
    top_descriptions: list[ChartEntry]
    top_reason_descriptions: list[ChartEntry]
