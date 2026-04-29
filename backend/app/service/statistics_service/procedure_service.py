from sqlalchemy.orm import Session

from repository.statistics_repository.procedure_repository import ProcedureRepository
from domain.schemas.statistics_schemas.patient_schema import ChartEntry
from domain.schemas.statistics_schemas.condition_schema import PerPatientStats
from domain.schemas.statistics_schemas.procedure_schema import ProcedureStatisticsResponse


class ProcedureService:
    def __init__(self, db: Session, range_str: str = "all"):
        self.repo = ProcedureRepository(db, range_str)

    def get_procedure_summary(self) -> ProcedureStatisticsResponse:
        total = self.repo.get_total_procedures()
        per_patient = self.repo.get_per_patient_stats()

        return ProcedureStatisticsResponse(
            total_procedures=total,
            unique_procedures=self.repo.get_unique_procedures(),
            per_patient=PerPatientStats(**per_patient),
            top_procedures=self._to_chart_entries(
                self.repo.get_top_procedures(total=total), "procedure"
            ),
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
