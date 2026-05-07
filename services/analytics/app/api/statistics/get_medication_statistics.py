from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from .statistics_router import statistics_router
from service.statistics_service.medication_service import MedicationService
from domain.schemas.statistics_schemas.medication_schema import MedicationStatisticsResponse


@statistics_router.get("/medications", response_model=MedicationStatisticsResponse)
async def get_medication_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = MedicationService(db, range)
    return service.get_medication_summary()
