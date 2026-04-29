from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import MedicationItem
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router
from api._scope import Scope, scope_dep, require_patient_access


@patient_router.get("/{patient_id}/medications", response_model=List[MedicationItem])
async def get_patient_medications(
    patient_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    return PatientService(PatientRepository(db)).get_patient_medications(patient_id)
