from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientDetailResponse
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router


@patient_router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    try:
        return PatientService(PatientRepository(db)).get_patient(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
