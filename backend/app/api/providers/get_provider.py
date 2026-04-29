from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ProviderDetailResponse
from repository import ProviderRepository
from service import ProviderService
from .provider_router import provider_router


@provider_router.get("/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ProviderService(ProviderRepository(db)).get_provider(provider_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
