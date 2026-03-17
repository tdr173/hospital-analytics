from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.procedure_service import ProcedureService
from app.domain.schemas.statistics_schema.procedure_schema import ProcedureStatisticsResponse


@statistics_router.get("/procedures", response_model=ProcedureStatisticsResponse)
async def get_procedure_statistics(db: Session = Depends(get_db)):
    service = ProcedureService(db)
    return service.get_procedure_summary()
