from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.encounter_service import EncounterService
from domain.schemas.statistics_schemas.encounter_schema import EncounterStatisticsResponse


@statistics_router.get("/encounters", response_model=EncounterStatisticsResponse)
async def get_encounter_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = EncounterService(db, range, provider_id)
    return service.get_encounter_summary()
