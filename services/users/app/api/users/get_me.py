from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.user_schemas.user_schema import UserProfileResponse
from repository.user_repository import UserRepository
from service.user_service import UserService
from api._scope import Scope, scope_dep
from .users_router import users_router


@users_router.get("/me", response_model=UserProfileResponse)
async def get_me(
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    from fastapi import HTTPException
    if not scope.role:
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = scope.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return UserService(UserRepository(db)).get_profile_internal(int(user_id))
