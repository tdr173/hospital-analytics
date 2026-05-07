from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import EncounterObservationItem, PagedResponse
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router


@encounter_router.get("/{encounter_id}/observations", response_model=PagedResponse[EncounterObservationItem])
async def get_encounter_observations(
    encounter_id: str,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    items, has_more = EncounterService(EncounterRepository(db)).get_encounter_observations(encounter_id, page)
    return PagedResponse(items=items, has_more=has_more)
