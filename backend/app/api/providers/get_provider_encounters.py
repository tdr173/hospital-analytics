from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ProviderEncounterItem
from repository import ProviderRepository
from service import ProviderService
from .provider_router import provider_router


@provider_router.get("/{provider_id}/encounters", response_model=List[ProviderEncounterItem])
async def get_provider_encounters(provider_id: str, db: Session = Depends(get_db)):
    return ProviderService(ProviderRepository(db)).get_provider_encounters(provider_id)
