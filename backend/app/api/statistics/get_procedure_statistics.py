from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.procedure_service import ProcedureService
from domain.schemas.statistics_schemas.procedure_schema import ProcedureStatisticsResponse


@statistics_router.get("/procedures", response_model=ProcedureStatisticsResponse)
async def get_procedure_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = ProcedureService(db, range, provider_id)
    return service.get_procedure_summary()
