from pydantic import BaseModel
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry


class DurationStatsEntry(BaseModel):
    name: str
    count: int
    min_duration: float
    max_duration: float
    avg_duration: float
    median_duration: float
    tooltip: str


class EncounterStatisticsResponse(BaseModel):
    total_encounters: int
    encounter_class: list[ChartEntry]
    duration_stats: list[DurationStatsEntry]
    top_descriptions: list[ChartEntry]
    top_reason_descriptions: list[ChartEntry]
