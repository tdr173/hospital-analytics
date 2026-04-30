from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.condition_service import ConditionService
from domain.schemas.statistics_schemas.condition_schema import ConditionStatisticsResponse


@statistics_router.get("/conditions", response_model=ConditionStatisticsResponse)
async def get_condition_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = ConditionService(db, range, provider_id)
    return service.get_condition_summary()
