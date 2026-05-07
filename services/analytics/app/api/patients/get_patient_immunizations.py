from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import ImmunizationItem, PagedResponse
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router
from api._scope import Scope, scope_dep, require_patient_access


@patient_router.get("/{patient_id}/immunizations", response_model=PagedResponse[ImmunizationItem])
async def get_patient_immunizations(
    patient_id: str,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_patient_access(scope, patient_id)
    items, has_more = PatientService(PatientRepository(db)).get_patient_immunizations(patient_id, page)
    return PagedResponse(items=items, has_more=has_more)
