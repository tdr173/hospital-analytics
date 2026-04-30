from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.immunization_service import ImmunizationService
from domain.schemas.statistics_schemas.immunization_schema import ImmunizationStatisticsResponse


@statistics_router.get("/immunizations", response_model=ImmunizationStatisticsResponse)
async def get_immunization_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = ImmunizationService(db, range, provider_id)
    return service.get_immunization_summary()
