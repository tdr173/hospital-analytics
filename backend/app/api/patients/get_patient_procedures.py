from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ProcedureItem
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router


@patient_router.get("/{patient_id}/procedures", response_model=List[ProcedureItem])
async def get_patient_procedures(patient_id: str, db: Session = Depends(get_db)):
    return PatientService(PatientRepository(db)).get_patient_procedures(patient_id)
