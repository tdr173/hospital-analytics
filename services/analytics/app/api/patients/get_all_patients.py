from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientListResponse
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router
from api._scope import Scope, scope_dep

import re

def _to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


@patient_router.get("", response_model=PatientListResponse)
async def get_patients(
    search: Optional[str] = None,
    gender: Optional[str] = None,
    age_group: Optional[str] = Query(None, alias="ageGroup"),
    status: Optional[str] = None,
    race: Optional[str] = None,
    marital: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    rows: int = 25,
    sort_by: str = Query("lastName", alias="sortBy"),
    sort_type: str = Query("asc", alias="sortType"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    service = PatientService(PatientRepository(db))
    return service.get_patients(
        search=search,
        gender=gender,
        age_group=age_group,
        status=status,
        race=race,
        marital=marital,
        city=city,
        page=page,
        rows=rows,
        sort_by=_to_snake(sort_by),
        sort_type=sort_type,
        role=scope.role,
        patient_id_scope=scope.patient_id,
        provider_id_scope=scope.provider_id,
    )
