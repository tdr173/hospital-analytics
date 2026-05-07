from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.encounter_service import EncounterService
from domain.schemas.statistics_schemas.encounter_schema import EncounterStatisticsResponse


@statistics_router.get("/encounters", response_model=EncounterStatisticsResponse)
async def get_encounter_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = EncounterService(db, range)
    return service.get_encounter_summary()
