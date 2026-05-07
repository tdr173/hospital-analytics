from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import LoginRequest, LoginResponse
from repository import AuthRepository
from service import AuthService
from .auth_router import auth_router


@auth_router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(AuthRepository(db)).login(payload)
