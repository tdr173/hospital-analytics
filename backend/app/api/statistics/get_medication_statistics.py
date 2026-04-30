from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.medication_service import MedicationService
from domain.schemas.statistics_schemas.medication_schema import MedicationStatisticsResponse


@statistics_router.get("/medications", response_model=MedicationStatisticsResponse)
async def get_medication_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = MedicationService(db, range, provider_id)
    return service.get_medication_summary()
