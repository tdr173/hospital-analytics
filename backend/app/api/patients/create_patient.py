from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientDetailResponse
from domain.schemas.patient_schemas.patient_schema import PatientCreateRequest
from repository import PatientRepository, AuthRepository
from service import PatientService, AuthService
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
    try:
        result = PatientService(PatientRepository(db)).create_patient(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if payload.email:
        AuthService(AuthRepository(db)).create_account_for_patient(
            email=payload.email,
            patient_id=result.patient_id,
        )

    return result
