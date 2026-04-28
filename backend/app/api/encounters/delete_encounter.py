from fastapi import Depends, HTTPException, Response
from sqlalchemy.orm import Session

from db.db_connector import get_db
from repository import EncounterRepository
from service import EncounterService
from api._scope import Scope, scope_dep
from .encounter_router import encounter_router


@encounter_router.delete("/{encounter_id}", status_code=204)
async def delete_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot delete encounters")
    provider_id_scope = scope.provider_id if scope.is_doctor else None
    try:
        EncounterService(EncounterRepository(db)).delete_encounter(encounter_id, provider_id_scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        msg = str(e)
        status = 409 if "cannot delete" in msg else 404
        raise HTTPException(status_code=status, detail=msg)
    return Response(status_code=204)
