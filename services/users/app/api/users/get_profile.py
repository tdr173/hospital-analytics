"""Internal endpoint called by auth-service at login to get role + entity IDs.
Only reachable within the docker network (not exposed via Traefik with auth).
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.user_schemas.user_schema import UserProfileResponse
from repository.user_repository import UserRepository
from service.user_service import UserService
from .users_router import users_router


@users_router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: int, db: Session = Depends(get_db)):
    return UserService(UserRepository(db)).get_profile_internal(user_id)
