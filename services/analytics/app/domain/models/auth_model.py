from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class UserRole(str, Enum):
    MANAGER = "MANAGER"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class AuthModel(SQLModel, table=True):
    __tablename__ = "auth_user"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(nullable=False, unique=True, index=True, max_length=120)
    password: str = Field(nullable=False, max_length=120)  # bcrypt hash
    role: UserRole = Field(nullable=False, default=UserRole.PATIENT)
    # Link to a clinical entity. At most one of these is set:
    #   - DOCTOR / MANAGER role -> provider_id
    #   - PATIENT role -> patient_id
    #   - MANAGER without provider_id is allowed (admin without a clinical record)
    # Cross-service references. Lives in auth_db; the actual patient/provider
    # rows live in clinical_db. Validated by application logic + sync events,
    # not a DB-level FK constraint.
    patient_id: Optional[str] = Field(default=None, index=True)
    provider_id: Optional[str] = Field(default=None, index=True)
    must_change_password: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
