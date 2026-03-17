from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.medication_service import MedicationService
from app.domain.schemas.statistics_schema.medication_schema import MedicationStatisticsResponse


@statistics_router.get("/medications", response_model=MedicationStatisticsResponse)
async def get_medication_statistics(db: Session = Depends(get_db)):
    service = MedicationService(db)
    return service.get_medication_summary()
