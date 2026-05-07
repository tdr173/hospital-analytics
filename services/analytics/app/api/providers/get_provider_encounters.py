from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import ProviderEncounterPageResponse
from repository import ProviderRepository
from service import ProviderService
from .provider_router import provider_router


@provider_router.get("/{provider_id}/encounters", response_model=ProviderEncounterPageResponse)
async def get_provider_encounters(
    provider_id: str,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    items, has_more = ProviderService(ProviderRepository(db)).get_provider_encounters(
        provider_id, page=page, page_size=20
    )
    return ProviderEncounterPageResponse(items=items, has_more=has_more)
