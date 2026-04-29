from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterMedicationItem
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router


@encounter_router.get("/{encounter_id}/medications", response_model=List[EncounterMedicationItem])
async def get_encounter_medications(encounter_id: str, db: Session = Depends(get_db)):
    return EncounterService(EncounterRepository(db)).get_encounter_medications(encounter_id)
