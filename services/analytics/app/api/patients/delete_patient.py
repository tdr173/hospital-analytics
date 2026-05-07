from fastapi import Depends, HTTPException, Response
from sqlalchemy.orm import Session

from db.db_connector import get_db
from repository import PatientRepository
from service import PatientService
from api._scope import Scope, scope_dep
from .patient_router import patient_router


@patient_router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot delete patient records")
    try:
        PatientService(PatientRepository(db)).delete_patient(patient_id)
    except ValueError as e:
        msg = str(e)
        status = 409 if "cannot delete" in msg else 404
        raise HTTPException(status_code=status, detail=msg)
    return Response(status_code=204)
