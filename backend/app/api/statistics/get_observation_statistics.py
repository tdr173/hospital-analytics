from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.observation_service import ObservationService
from domain.schemas.statistics_schemas.observation_schema import ObservationStatisticsResponse


@statistics_router.get("/observations", response_model=ObservationStatisticsResponse)
async def get_observation_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = ObservationService(db, range, provider_id)
    return service.get_observation_summary()
