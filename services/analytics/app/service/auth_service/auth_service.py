"""Authentication service.

Handles login, set-password, and account-invite flows. The invite flow is
called from the patient/provider create endpoints when an email is provided
on the create payload: a temporary "partial" password is generated, hashed,
stored, and emailed to the new user along with a link to set their real
password.
"""
from __future__ import annotations

import logging
import os
import secrets
import string
from typing import Optional

import bcrypt
from fastapi import HTTPException
from starlette import status

from domain import AuthModel, UserRole
from domain.schemas.auth_schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    SetPasswordRequest,
    CurrentUserResponse,
)
from repository import AuthRepository
from api._security import create_access_token
from mail_sender import send_mail, MailSendError

logger = logging.getLogger(__name__)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _generate_partial_password(length: int = 12) -> str:
    """Random alphanumeric password with mixed case + digits.

    Avoids ambiguous characters (0/O, 1/l/I) so users can transcribe it
    from the email if their mail client mangles formatting.
    """
    alphabet = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def _send_invite_email(email: str, partial_password: str) -> None:
    """Best-effort send. Logs and swallows so a broken SMTP doesn't block
    account creation. The temporary password is still persisted, so the
    admin can resend or share it manually."""
    link = f"{_frontend_url()}/set-password?email={email}"
    body = (
        "Welcome to Hospital Analytics.\n\n"
        "An account has been created for you. Use the temporary password below\n"
        "to set your permanent password.\n\n"
        f"Temporary password: {partial_password}\n\n"
        f"Set your new password here:\n{link}\n\n"
        "This temporary password is single-use. After you set your new password,\n"
        "log in normally with that one.\n"
    )
    html = (
        "<p>Welcome to Hospital Analytics.</p>"
        "<p>An account has been created for you. Use the temporary password below "
        "to set your permanent password.</p>"
        f"<p><b>Temporary password:</b> <code>{partial_password}</code></p>"
        f'<p><a href="{link}">Set your new password</a></p>'
        "<p style=\"color:#6b7280;font-size:0.85em\">This temporary password is single-use. "
        "After you set your new password, log in normally with that one.</p>"
    )
    try:
        send_mail(
            to=email,
            subject="Set your Hospital Analytics password",
            body=body,
            html=html,
        )
    except MailSendError as e:
        logger.warning("Invite email send failed for %s: %s", email, e)


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def login(self, dto: LoginRequest) -> LoginResponse:
        user = self.repo.get_by_email(dto.email)
        if not user or not _verify_password(dto.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token = create_access_token(
            user.user_id,
            user.role.value if isinstance(user.role, UserRole) else str(user.role),
            email=user.email,
            patient_id=user.patient_id,
            provider_id=user.provider_id,
        )
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            role=user.role.value if isinstance(user.role, UserRole) else str(user.role),
            must_change_password=user.must_change_password,
            patient_id=user.patient_id,
            provider_id=user.provider_id,
            email=user.email,
        )

    def set_password(self, dto: SetPasswordRequest) -> dict:
        user = self.repo.get_by_email(dto.email)
        # Identical error message for "user not found" and "wrong temp password"
        # to avoid email enumeration.
        invalid = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or temporary password",
        )
        if not user or not user.must_change_password:
            raise invalid
        if not _verify_password(dto.temp_password, user.password):
            raise invalid
        if dto.new_password == dto.temp_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from the temporary password",
            )
        self.repo.update_password(user, _hash_password(dto.new_password))
        return {"success": True}

    def me(self, jwt_user: dict) -> CurrentUserResponse:
        user_id = jwt_user.get("user_id")
        user = self.repo.get_by_id(int(user_id)) if user_id else None
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return CurrentUserResponse(
            email=user.email,
            role=user.role.value if isinstance(user.role, UserRole) else str(user.role),
            must_change_password=user.must_change_password,
            patient_id=user.patient_id,
            provider_id=user.provider_id,
        )

    def create_account_for_patient(self, email: str, patient_id: str) -> Optional[AuthModel]:
        return self._create_invited_account(
            email=email,
            role=UserRole.PATIENT,
            patient_id=patient_id,
            provider_id=None,
        )

    def create_account_for_provider(
        self,
        email: str,
        provider_id: str,
        role: UserRole = UserRole.DOCTOR,
    ) -> Optional[AuthModel]:
        return self._create_invited_account(
            email=email,
            role=role,
            patient_id=None,
            provider_id=provider_id,
        )

    def _create_invited_account(
        self,
        *,
        email: str,
        role: UserRole,
        patient_id: Optional[str],
        provider_id: Optional[str],
    ) -> Optional[AuthModel]:
        if self.repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An auth account with this email already exists",
            )
        partial = _generate_partial_password()
        instance = self.repo.create(
            email=email,
            password_hash=_hash_password(partial),
            role=role,
            patient_id=patient_id,
            provider_id=provider_id,
            must_change_password=True,
        )
        _send_invite_email(email, partial)
        return instance
