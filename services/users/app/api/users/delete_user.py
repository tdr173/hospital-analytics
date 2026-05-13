from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from repository.user_repository import UserRepository
from service.user_service import UserService
from api._scope import Scope, scope_dep, require_manager
from .users_router import users_router


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    UserService(UserRepository(db)).delete_user(user_id)
