from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.patient_service import PatientService
from domain.schemas.statistics_schemas.patient_schema import PatientStatisticsResponse


@statistics_router.get("/patients", response_model=PatientStatisticsResponse)
async def get_patient_statistics(db: Session = Depends(get_db)):
    service = PatientService(db)
    return service.get_patient_summary()
