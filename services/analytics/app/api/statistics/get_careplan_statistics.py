from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from .statistics_router import statistics_router
from service.statistics_service.careplan_service import CarePlanService
from domain.schemas.statistics_schemas.careplan_schema import CarePlanStatisticsResponse


@statistics_router.get("/careplans", response_model=CarePlanStatisticsResponse)
async def get_careplan_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = CarePlanService(db, range)
    return service.get_careplan_summary()
