from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain.schemas.auth_schemas.auth_schema import ForgotPasswordRequest
from repository import AuthRepository
from service import AuthService
from .auth_router import auth_router


@auth_router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return AuthService(AuthRepository(db)).forgot_password(payload.email)
