from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.user_schemas.user_schema import UserProfileResponse, UserProfileUpdate
from repository.user_repository import UserRepository
from service.user_service import UserService
from api._scope import Scope, scope_dep
from .users_router import users_router


@users_router.patch("/{user_id}", response_model=UserProfileResponse)
async def update_user(
    user_id: int,
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    return UserService(UserRepository(db)).update_user(scope, user_id, payload)
