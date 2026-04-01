from sqlalchemy.orm import Session

from repository import ObservationRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats
from domain.schemas.statistics_schemas.observation_schema import (
    NumericStatsEntry,
    CategoricalStatsEntry,
    ObservationStatisticsResponse,
)


class ObservationService:
    def __init__(self, db: Session):
        self.repo = ObservationRepository(db)

    def get_observation_summary(self) -> ObservationStatisticsResponse:
        per_patient = self.repo.get_per_patient_stats()

        return ObservationStatisticsResponse(
            total_observations=self.repo.get_total_observations(),
            unique_observation_types=self.repo.get_unique_observation_types(),
            per_patient=PerPatientStats(**per_patient),
            top_observation_types=self._to_chart_entries(
                self.repo.get_top_observation_types(), "observation"
            ),
            numeric_stats=self._to_numeric_entries(self.repo.get_numeric_stats()),
            categorical_stats=self._to_categorical_entries(self.repo.get_categorical_stats()),
        )

    @staticmethod
    def _to_chart_entries(rows: list[dict], category: str) -> list[ChartEntry]:
        return [
            ChartEntry(
                name=row["label"] or "Unknown",
                value=row["count"],
                tooltip=f"{row['label'] or 'Unknown'}: {row['count']} ({row['percentage']}%)",
            )
            for row in rows
        ]

    @staticmethod
    def _to_categorical_entries(rows: list[dict]) -> list[CategoricalStatsEntry]:
        return [
            CategoricalStatsEntry(
                name=row["label"],
                count=row["count"],
                patient_count=row["patient_count"],
                percentage=row["percentage"],
                distinct_values=row["distinct_values"],
                tooltip=f"{row['label']}: {row['patient_count']} patients ({row['percentage']}%), {row['distinct_values']} distinct values",
            )
            for row in rows
        ]

    @staticmethod
    def _to_numeric_entries(rows: list[dict]) -> list[NumericStatsEntry]:
        return [
            NumericStatsEntry(
                name=row["label"],
                count=row["count"],
                patient_count=row["patient_count"],
                percentage=row["percentage"],
                min_value=row["min_value"],
                max_value=row["max_value"],
                avg_value=row["avg_value"],
                units=row["units"],
                tooltip=(
                    f"{row['label']}: avg {row['avg_value']} {row['units']}, "
                    f"range {row['min_value']}-{row['max_value']}"
                ),
            )
            for row in rows
        ]
