from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientDetailResponse
from domain.schemas.patient_schemas.patient_schema import PatientCreateRequest
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep, require_doctor
from messaging import publish_event_nowait, EventAction
from .patient_router import patient_router


@patient_router.post("", response_model=PatientDetailResponse, status_code=201)
async def create_patient(
    payload: PatientCreateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_doctor(scope)
    try:
        result = PatientService(PatientRepository(db)).create_patient(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Cross-service sync: publish patient.created so auth-service can issue an
    # invite if an email was provided. Lives across DBs, so we go through
    # RabbitMQ instead of an in-process call.
    publish_event_nowait(
        "patient",
        EventAction.CREATED,
        patient_id=result.patient_id,
        extra={"email": payload.email} if payload.email else None,
    )

    return result
