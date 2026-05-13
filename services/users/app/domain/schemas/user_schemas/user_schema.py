from datetime import datetime
from typing import Optional, List

from pydantic import Field

from domain.schemas.camel_model import CamelModel


class UserProfileResponse(CamelModel):
    user_id: int
    email: str
    role: str
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserProfileUpdate(CamelModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None


class UserListResponse(CamelModel):
    items: List[UserProfileResponse]
    total: int
