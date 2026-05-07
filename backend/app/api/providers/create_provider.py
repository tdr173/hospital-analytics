from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import ProviderDetailResponse
from domain.schemas.provider_schemas.provider_schema import ProviderCreateRequest
from repository import ProviderRepository, AuthRepository
from service import ProviderService, AuthService
from api._scope import Scope, scope_dep, require_manager
from .provider_router import provider_router


@provider_router.post("", response_model=ProviderDetailResponse, status_code=201)
async def create_provider(
    payload: ProviderCreateRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    try:
        result = ProviderService(ProviderRepository(db)).create_provider(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if payload.email:
        AuthService(AuthRepository(db)).create_account_for_provider(
            email=payload.email,
            provider_id=result.provider_id,
        )

    return result
