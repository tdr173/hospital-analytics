from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.user_schemas.user_schema import UserListResponse
from repository.user_repository import UserRepository
from service.user_service import UserService
from api._scope import Scope, scope_dep, require_manager
from .users_router import users_router


@users_router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    rows: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    return UserService(UserRepository(db)).list_users(page=page, rows=rows)
