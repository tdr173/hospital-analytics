from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterDetailResponse
from repository import EncounterRepository
from service import EncounterService
from .encounter_router import encounter_router


@encounter_router.get("/{encounter_id}", response_model=EncounterDetailResponse)
async def get_encounter(encounter_id: str, db: Session = Depends(get_db)):
    try:
        return EncounterService(EncounterRepository(db)).get_encounter(encounter_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
