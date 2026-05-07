from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import ProviderDetailResponse
from domain.schemas.provider_schemas.provider_schema import ProviderUpdateRequest
from repository import ProviderRepository
from service import ProviderService
from api._scope import Scope, scope_dep, require_manager
from .provider_router import provider_router


@provider_router.patch("/{provider_id}", response_model=ProviderDetailResponse)
async def update_provider(
    provider_id: str,
    payload: ProviderUpdateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    try:
        return ProviderService(ProviderRepository(db)).update_provider(provider_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
