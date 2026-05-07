from fastapi import Depends, HTTPException, Response
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from repository import ProviderRepository
from service import ProviderService
from api._scope import Scope, scope_dep, require_manager
from .provider_router import provider_router


@provider_router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    try:
        ProviderService(ProviderRepository(db)).delete_provider(provider_id)
    except ValueError as e:
        msg = str(e)
        status = 409 if "cannot delete" in msg else 404
        raise HTTPException(status_code=status, detail=msg)
    return Response(status_code=204)
