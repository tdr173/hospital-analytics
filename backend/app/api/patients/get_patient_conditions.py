from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ConditionItem
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router
from api._scope import Scope, scope_dep, require_patient_access


@patient_router.get("/{patient_id}/conditions", response_model=List[ConditionItem])
async def get_patient_conditions(
    patient_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    return PatientService(PatientRepository(db)).get_patient_conditions(patient_id)
