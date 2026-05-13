from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import RegisterRequest
from repository import AuthRepository
from service import AuthService
from .auth_router import auth_router


@auth_router.post("/register", status_code=201)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(AuthRepository(db)).register(payload)
