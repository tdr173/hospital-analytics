from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterAllergyItem
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router


@encounter_router.get("/{encounter_id}/allergies", response_model=List[EncounterAllergyItem])
async def get_encounter_allergies(encounter_id: str, db: Session = Depends(get_db)):
    return EncounterService(EncounterRepository(db)).get_encounter_allergies(encounter_id)
