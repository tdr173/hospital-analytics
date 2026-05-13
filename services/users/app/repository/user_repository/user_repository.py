from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from domain.models.user_profile_model import UserProfile


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.email == email).first()

    def list_all(self, page: int = 1, rows: int = 25) -> Tuple[List[UserProfile], int]:
        query = self.db.query(UserProfile)
        total = query.count()
        items = query.offset((page - 1) * rows).limit(rows).all()
        return items, total

    def create(
        self,
        *,
        user_id: int,
        email: str,
        role: str,
        patient_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        display_name: Optional[str] = None,
        phone: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> UserProfile:
        from domain.models.auth_model import UserRole
        instance = UserProfile(
            user_id=user_id,
            email=email,
            role=UserRole(role),
            patient_id=patient_id,
            provider_id=provider_id,
            display_name=display_name,
            phone=phone,
            job_title=job_title,
        )
        self.db.add(instance)
        self._commit()
        self.db.refresh(instance)
        return instance

    def update(self, profile: UserProfile, **fields) -> UserProfile:
        for key, value in fields.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        self._commit()
        self.db.refresh(profile)
        return profile

    def delete_by_user_id(self, user_id: int) -> None:
        profile = self.get_by_user_id(user_id)
        if profile:
            self.db.delete(profile)
            self._commit()

    def delete_by_patient_id(self, patient_id: str) -> None:
        profile = self.db.query(UserProfile).filter(UserProfile.patient_id == patient_id).first()
        if profile:
            self.db.delete(profile)
            self._commit()

    def delete_by_provider_id(self, provider_id: str) -> None:
        profile = self.db.query(UserProfile).filter(UserProfile.provider_id == provider_id).first()
        if profile:
            self.db.delete(profile)
            self._commit()
