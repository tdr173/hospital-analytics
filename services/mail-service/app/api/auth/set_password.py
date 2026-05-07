from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import SetPasswordRequest
from repository import AuthRepository
from service import AuthService
from .auth_router import auth_router


@auth_router.post("/set-password")
async def set_password(payload: SetPasswordRequest, db: Session = Depends(get_db)):
    return AuthService(AuthRepository(db)).set_password(payload)
