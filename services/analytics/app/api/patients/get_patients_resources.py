from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientResourcesResponse
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router


@patient_router.get("/resources", response_model=PatientResourcesResponse)
async def get_patients_resources(db: Session = Depends(get_db)):
    service = PatientService(PatientRepository(db))
    return service.get_patient_resources()
