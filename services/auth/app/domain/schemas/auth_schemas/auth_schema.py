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
    """Token-based password set/reset.

    The token is a short-lived JWT (10 min) with `purpose=password_reset`,
    issued by /auth/forgot-password or by the invite flow when an account is
    auto-provisioned via patient.created / provider.created.
    """
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=120)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class CurrentUserResponse(CamelModel):
    email: str
    role: str
    must_change_password: bool
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
