from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import AllergyItem
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router


@patient_router.get("/{patient_id}/allergies", response_model=List[AllergyItem])
async def get_patient_allergies(patient_id: str, db: Session = Depends(get_db)):
    return PatientService(PatientRepository(db)).get_patient_allergies(patient_id)
