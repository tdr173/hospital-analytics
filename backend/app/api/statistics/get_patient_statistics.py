from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.patient_service import PatientService
from app.domain.schemas.statistics_schema.patient_schema import PatientStatisticsResponse


@statistics_router.get("/patients", response_model=PatientStatisticsResponse)
async def get_patient_statistics(db: Session = Depends(get_db)):
    service = PatientService(db)
    return service.get_patient_summary()
