from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from domain import AuthModel


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def _commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def email_exists(self, email: str) -> bool:
        return self.db.query(AuthModel).filter(AuthModel.email == email).count() > 0

    def get_by_email(self, email: str) -> Optional[AuthModel]:
        return self.db.query(AuthModel).filter(AuthModel.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[AuthModel]:
        return self.db.query(AuthModel).filter(AuthModel.user_id == user_id).first()

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        must_change_password: bool = True,
    ) -> AuthModel:
        instance = AuthModel(
            email=email,
            password=password_hash,
            must_change_password=must_change_password,
        )
        self.db.add(instance)
        self._commit()
        self.db.refresh(instance)
        return instance

    def update_password(self, user: AuthModel, new_password_hash: str) -> AuthModel:
        user.password = new_password_hash
        user.must_change_password = False
        self._commit()
        self.db.refresh(user)
        return user

    def delete_by_id(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self._commit()

    def delete(self, user: AuthModel) -> None:
        self.db.delete(user)
        self._commit()
