from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.immunization_service import ImmunizationService
from app.domain.schemas.statistics_schema.immunization_schema import ImmunizationStatisticsResponse


@statistics_router.get("/immunizations", response_model=ImmunizationStatisticsResponse)
async def get_immunization_statistics(db: Session = Depends(get_db)):
    service = ImmunizationService(db)
    return service.get_immunization_summary()
