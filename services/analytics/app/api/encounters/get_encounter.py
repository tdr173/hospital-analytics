from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import EncounterDetailResponse
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router
from api._scope import Scope, scope_dep


@encounter_router.get("/{encounter_id}", response_model=EncounterDetailResponse)
async def get_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    try:
        detail = EncounterService(EncounterRepository(db)).get_encounter(encounter_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if scope.is_patient and scope.patient_id and detail.patient_id != scope.patient_id:
        raise HTTPException(status_code=403, detail="Patient may only view their own encounters")
    if scope.is_doctor and scope.provider_id and detail.provider_id != scope.provider_id:
        raise HTTPException(status_code=403, detail="Doctor may only view their own encounters")
    return detail
