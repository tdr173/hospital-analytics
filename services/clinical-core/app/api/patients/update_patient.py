from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientDetailResponse
from domain.schemas.patient_schemas.patient_schema import PatientUpdateRequest
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep, require_doctor
from .patient_router import patient_router


@patient_router.patch("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient(
    patient_id: str,
    payload: PatientUpdateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_doctor(scope)
    try:
        return PatientService(PatientRepository(db)).update_patient(patient_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
