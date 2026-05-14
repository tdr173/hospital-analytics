from typing import List

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import SequenceContinuationItem
from repository import SequenceRepository
from service import SequenceService
from .patient_router import patient_router
from api._scope import Scope, scope_dep, require_patient_access


@patient_router.get("/{patient_id}/continuations", response_model=List[SequenceContinuationItem])
async def get_patient_continuations(
    patient_id: str,
    min_matched: int = Query(2, ge=1),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    return SequenceService(SequenceRepository(db)).get_patient_continuations(patient_id, min_matched)
