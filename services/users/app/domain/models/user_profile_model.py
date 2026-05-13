from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from .auth_model import UserRole


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profile"

    user_id: int = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    role: UserRole
    patient_id: Optional[str] = Field(default=None, index=True)
    provider_id: Optional[str] = Field(default=None, index=True)
    display_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
