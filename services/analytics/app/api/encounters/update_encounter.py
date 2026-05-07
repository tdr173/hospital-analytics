from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import EncounterDetailResponse
from domain.schemas.encounter_schemas.encounter_schema import EncounterUpdateRequest
from repository import EncounterRepository
from service import EncounterService
from api._scope import Scope, scope_dep
from messaging import publish_event_nowait, EventAction
from .encounter_router import encounter_router


@encounter_router.patch("/{encounter_id}", response_model=EncounterDetailResponse)
async def update_encounter(
    encounter_id: str,
    payload: EncounterUpdateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot edit encounters")
    provider_id_scope = scope.provider_id if scope.is_doctor else None
    try:
        result = EncounterService(EncounterRepository(db)).update_encounter(encounter_id, payload, provider_id_scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    publish_event_nowait(
        "encounter", EventAction.UPDATED,
        patient_id=getattr(result, "patient_id", None),
        encounter_id=encounter_id,
    )
    return result
