from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterDetailResponse
from domain.schemas.encounter_schemas.encounter_schema import EncounterCreateRequest
from repository import EncounterRepository
from service import EncounterService
from api._scope import Scope, scope_dep
from .encounter_router import encounter_router


@encounter_router.post("", response_model=EncounterDetailResponse, status_code=201)
async def create_encounter(
    payload: EncounterCreateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot create encounters")
    provider_id_scope = scope.provider_id if scope.is_doctor else None
    try:
        return EncounterService(EncounterRepository(db)).create_encounter(payload, provider_id_scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
