from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import CurrentUserResponse
from repository import AuthRepository
from service import AuthService
from api._security import get_current_user
from .auth_router import auth_router


@auth_router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    db: Session = Depends(get_db),
    jwt_user: dict = Depends(get_current_user),
):
    return AuthService(AuthRepository(db)).me(jwt_user)
