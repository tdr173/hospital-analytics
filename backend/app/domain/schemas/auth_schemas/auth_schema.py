from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from domain.schemas.camel_model import CamelModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=120)


class LoginResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    must_change_password: bool
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    email: str


class SetPasswordRequest(BaseModel):
    email: EmailStr
    temp_password: str = Field(min_length=1, max_length=120)
    new_password: str = Field(min_length=8, max_length=120)


class CurrentUserResponse(CamelModel):
    email: str
    role: str
    must_change_password: bool
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
