from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import EncounterResourcesResponse
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router


@encounter_router.get("/resources", response_model=EncounterResourcesResponse)
async def get_encounters_resources(db: Session = Depends(get_db)):
    return EncounterService(EncounterRepository(db)).get_encounter_resources()
