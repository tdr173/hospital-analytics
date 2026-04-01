from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.observation_service import ObservationService
from domain.schemas.statistics_schemas.observation_schema import ObservationStatisticsResponse


@statistics_router.get("/observations", response_model=ObservationStatisticsResponse)
async def get_observation_statistics(db: Session = Depends(get_db)):
    service = ObservationService(db)
    return service.get_observation_summary()
