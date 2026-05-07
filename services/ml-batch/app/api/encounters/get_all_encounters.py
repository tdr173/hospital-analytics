from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session
import re

from db.db_connector import get_db
from domain import EncounterListResponse
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router
from api._scope import Scope, scope_dep


def _to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


@encounter_router.get("", response_model=EncounterListResponse)
async def get_encounters(
    search: Optional[str] = None,
    encounter_class: Optional[str] = Query(None, alias="encounterClass"),
    date_from: Optional[str] = Query(None, alias="dateFrom"),
    date_to: Optional[str] = Query(None, alias="dateTo"),
    page: int = 1,
    rows: int = 25,
    sort_by: str = Query("startDate", alias="sortBy"),
    sort_type: str = Query("desc", alias="sortType"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    return EncounterService(EncounterRepository(db)).get_encounters(
        search=search,
        encounter_class=encounter_class,
        date_from=date_from,
        date_to=date_to,
        page=page,
        rows=rows,
        sort_by=_to_snake(sort_by),
        sort_type=sort_type,
        role=scope.role,
        patient_id_scope=scope.patient_id,
        provider_id_scope=scope.provider_id,
    )
