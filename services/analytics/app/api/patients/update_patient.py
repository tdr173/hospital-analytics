from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import PatientDetailResponse
from domain.schemas.patient_schemas.patient_schema import PatientUpdateRequest
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep
from .patient_router import patient_router


@patient_router.patch("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient(
    patient_id: str,
    payload: PatientUpdateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot edit patient records")
    try:
        return PatientService(PatientRepository(db)).update_patient(patient_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
