from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientDetailResponse
from domain.schemas.patient_schemas.patient_schema import PatientCreateRequest
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep
from .patient_router import patient_router


@patient_router.post("", response_model=PatientDetailResponse, status_code=201)
async def create_patient(
    payload: PatientCreateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot create patient records")
    # a doctor only sees patients in their patient_provider panel, so attach the
    # new patient to them; managers see everyone and need no association
    provider_id_scope = scope.provider_id if scope.is_doctor else None
    try:
        return PatientService(PatientRepository(db)).create_patient(payload, provider_id_scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
