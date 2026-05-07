from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.procedure_service import ProcedureService
from domain.schemas.statistics_schemas.procedure_schema import ProcedureStatisticsResponse


@statistics_router.get("/procedures", response_model=ProcedureStatisticsResponse)
async def get_procedure_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = ProcedureService(db, range)
    return service.get_procedure_summary()
