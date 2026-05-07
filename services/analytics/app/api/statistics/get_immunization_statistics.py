from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.immunization_service import ImmunizationService
from domain.schemas.statistics_schemas.immunization_schema import ImmunizationStatisticsResponse


@statistics_router.get("/immunizations", response_model=ImmunizationStatisticsResponse)
async def get_immunization_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = ImmunizationService(db, range)
    return service.get_immunization_summary()
