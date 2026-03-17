from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.encounter_service import EncounterService
from app.domain.schemas.statistics_schema.encounter_schema import EncounterStatisticsResponse


@statistics_router.get("/encounters", response_model=EncounterStatisticsResponse)
async def get_encounter_statistics(db: Session = Depends(get_db)):
    service = EncounterService(db)
    return service.get_encounter_summary()
