from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.observation_service import ObservationService
from app.domain.schemas.statistics_schema.observation_schema import ObservationStatisticsResponse


@statistics_router.get("/observations", response_model=ObservationStatisticsResponse)
async def get_observation_statistics(db: Session = Depends(get_db)):
    service = ObservationService(db)
    return service.get_observation_summary()
