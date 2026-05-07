from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ProviderResourcesResponse
from repository import ProviderRepository
from service import ProviderService
from .provider_router import provider_router


@provider_router.get("/resources", response_model=ProviderResourcesResponse)
async def get_providers_resources(db: Session = Depends(get_db)):
    return ProviderService(ProviderRepository(db)).get_provider_resources()
