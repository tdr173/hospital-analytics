from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.patient_schemas.patient_schema import PatientObservationItem
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep, require_patient_access
from .patient_router import patient_router


@patient_router.get("/{patient_id}/observations", response_model=List[PatientObservationItem])
async def get_patient_observations(
    patient_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    return PatientService(PatientRepository(db)).get_patient_observations(patient_id)
