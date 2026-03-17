from sqlalchemy.orm import Session

from app.repository.statistics_repository.procedure_repository import ProcedureRepository
from app.domain.schemas.statistics_schema.patient_schema import ChartEntry
from app.domain.schemas.statistics_schema.condition_schema import PerPatientStats
from app.domain.schemas.statistics_schema.procedure_schema import ProcedureStatisticsResponse


class ProcedureService:
    def __init__(self, db: Session):
        self.repo = ProcedureRepository(db)

    def get_procedure_summary(self) -> ProcedureStatisticsResponse:
        per_patient = self.repo.get_per_patient_stats()

        return ProcedureStatisticsResponse(
            total_procedures=self.repo.get_total_procedures(),
            unique_procedures=self.repo.get_unique_procedures(),
            per_patient=PerPatientStats(**per_patient),
            top_procedures=self._to_chart_entries(
                self.repo.get_top_procedures(), "procedure"
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
