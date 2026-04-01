from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.condition_service import ConditionService
from domain.schemas.statistics_schemas.condition_schema import ConditionStatisticsResponse


@statistics_router.get("/conditions", response_model=ConditionStatisticsResponse)
async def get_condition_statistics(db: Session = Depends(get_db)):
    service = ConditionService(db)
    return service.get_condition_summary()
