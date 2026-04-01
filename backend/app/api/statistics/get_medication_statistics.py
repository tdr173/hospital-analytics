from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.medication_service import MedicationService
from domain.schemas.statistics_schemas.medication_schema import MedicationStatisticsResponse


@statistics_router.get("/medications", response_model=MedicationStatisticsResponse)
async def get_medication_statistics(db: Session = Depends(get_db)):
    service = MedicationService(db)
    return service.get_medication_summary()
