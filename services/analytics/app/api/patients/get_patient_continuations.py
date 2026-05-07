from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import PatientContinuationItem, PagedResponse
from repository import SequenceRepository
from service import SequenceService
from .patient_router import patient_router
from api._scope import Scope, scope_dep, require_patient_access


@patient_router.get(
    "/{patient_id}/sequence-continuations",
    response_model=PagedResponse[PatientContinuationItem],
)
async def get_patient_continuations(
    patient_id: str,
    last_n: int = Query(3, ge=1, le=10, alias="lastN"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    items, has_more = SequenceService(SequenceRepository(db)).get_patient_continuations(
        patient_id=patient_id,
        last_n=last_n,
        page=page,
    )
    return PagedResponse(items=items, has_more=has_more)
