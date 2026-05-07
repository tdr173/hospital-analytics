from sqlalchemy.orm import Session

from repository.statistics_repository.encounter_repository import EncounterRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.encounter_schema import (
    DurationStatsEntry,
    EncounterStatisticsResponse,
)


class EncounterService:
    def __init__(self, db: Session, range_str: str = "all"):
        self.repo = EncounterRepository(db, range_str)

    def get_encounter_summary(self) -> EncounterStatisticsResponse:
        total = self.repo.get_total_encounters()

        return EncounterStatisticsResponse(
            total_encounters=total,
            encounter_class=self._to_chart_entries(
                self.repo.get_encounter_class_distribution(total), "encounter class"
            ),
            duration_stats=self._to_duration_entries(
                self.repo.get_duration_stats_per_class()
            ),
            top_descriptions=self._to_chart_entries(
                self.repo.get_top_descriptions(total=total), "description"
            ),
            top_reason_descriptions=self._to_chart_entries(
                self.repo.get_top_reason_descriptions(), "reason"
            ),
        )

    @staticmethod
    def _to_chart_entries(rows: list[dict], category: str) -> list[ChartEntry]:
        return [
            ChartEntry(
                name=row["label"] or "Unknown",
                value=row["count"],
                tooltip=f"{row['label'] or 'Unknown'}: {row['count']} encounters ({row['percentage']}%)",
            )
            for row in rows
        ]

    @staticmethod
    def _to_duration_entries(rows: list[dict]) -> list[DurationStatsEntry]:
        return [
            DurationStatsEntry(
                name=row["label"],
                count=row["count"],
                min_duration=row["min_duration"],
                max_duration=row["max_duration"],
                avg_duration=row["avg_duration"],
                median_duration=0,
                tooltip=(
                    f"{row['label']}: {row['count']} encounters, "
                    f"avg {row['avg_duration']} min, "
                    f"range {row['min_duration']}-{row['max_duration']} min"
                ),
            )
            for row in rows
        ]
