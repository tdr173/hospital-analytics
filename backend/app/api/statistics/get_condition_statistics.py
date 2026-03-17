from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.condition_service import ConditionService
from app.domain.schemas.statistics_schema.condition_schema import ConditionStatisticsResponse


@statistics_router.get("/conditions", response_model=ConditionStatisticsResponse)
async def get_condition_statistics(db: Session = Depends(get_db)):
    service = ConditionService(db)
    return service.get_condition_summary()
