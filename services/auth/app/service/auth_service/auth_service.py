"""Authentication service.

Handles login, registration, password set/reset, and account-invite flows.

auth_user stores only credentials (email, password). Role and profile data
live in users-service (users-db). Auth fetches profile via internal HTTP at
login time; all other cross-service communication is async via RabbitMQ.
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import httpx
import jwt
from fastapi import HTTPException
from starlette import status

from domain import AuthModel, UserRole
from domain.schemas.auth_schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    SetPasswordRequest,
    CurrentUserResponse,
)
from repository import AuthRepository
from mail_sender import send_mail, MailSendError

logger = logging.getLogger(__name__)

RESET_TOKEN_TTL_MINUTES = 10
RESET_TOKEN_PURPOSE = "password_reset"

_USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users:8000")


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _unusable_password_hash() -> str:
    return _hash_password(secrets.token_urlsafe(32))


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def _jwt_config() -> tuple[str, str]:
    secret = os.getenv("SECRET_KEY", "dev-insecure-change-me")
    algo = os.getenv("ALGORITHM", "HS256")
    return secret, algo


def _create_reset_token(user_id: int, email: str) -> str:
    secret, algo = _jwt_config()
    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": RESET_TOKEN_PURPOSE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, secret, algorithm=algo)


def _decode_reset_token(token: str) -> dict:
    secret, algo = _jwt_config()
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired token",
    )
    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
    except jwt.ExpiredSignatureError:
        raise invalid
    except jwt.InvalidTokenError:
        raise invalid
    if payload.get("purpose") != RESET_TOKEN_PURPOSE:
        raise invalid
    return payload


def _send_password_link_email(email: str, token: str, *, is_invite: bool) -> None:
    link = f"{_frontend_url()}/set-password?token={token}"
    if is_invite:
        subject = "Set your Hospital Analytics password"
        intro = ("Welcome to Hospital Analytics.\n\n"
                 "An account has been created for you. Click the link below "
                 "to set your password and log in.")
    else:
        subject = "Reset your Hospital Analytics password"
        intro = ("A password reset was requested for your Hospital Analytics "
                 "account. Click the link below to set a new password.")
    body = (
        f"{intro}\n\n"
        f"Set your password here:\n{link}\n\n"
        f"This link expires in {RESET_TOKEN_TTL_MINUTES} minutes.\n"
        "If you didn't request this, you can safely ignore the email.\n"
    )
    html = (
        f"<p>{intro.replace(chr(10) + chr(10), '</p><p>')}</p>"
        f'<p><a href="{link}">Set your password</a></p>'
        f'<p style="color:#6b7280;font-size:0.85em">This link expires in '
        f"{RESET_TOKEN_TTL_MINUTES} minutes. If you didn't request this, "
        "you can safely ignore the email.</p>"
    )
    try:
        send_mail(to=email, subject=subject, body=body, html=html)
    except MailSendError as e:
        logger.warning("password-link email failed for %s: %s", email, e)


def _fetch_user_profile(user_id: int) -> dict:
    """Synchronous HTTP call to users-service to get role + entity IDs."""
    url = f"{_USERS_SERVICE_URL}/users/profile/{user_id}"
    try:
        resp = httpx.get(url, timeout=5.0)
    except httpx.RequestError as exc:
        logger.error("users-service unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User profile service is temporarily unavailable.",
        )
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user profile found for these credentials.",
        )
    if not resp.is_success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User profile service returned an error.",
        )
    return resp.json()


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def register(self, dto: RegisterRequest) -> dict:
        from api._security import create_access_token
        from messaging import publish_event_nowait, EventAction

        if self.repo.email_exists(dto.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        instance = self.repo.create(
            email=dto.email,
            password_hash=_unusable_password_hash(),
            must_change_password=True,
        )
        token = _create_reset_token(instance.user_id, dto.email)

        publish_event_nowait(
            "user",
            EventAction.CREATED,
            extra={
                "user_id": instance.user_id,
                "email": dto.email,
                "role": dto.role,
                "patient_id": dto.patient_id,
                "provider_id": dto.provider_id,
                "display_name": dto.display_name,
                "phone": dto.phone,
                "job_title": dto.job_title,
                "invite_token": token,
            },
        )
        return {"user_id": instance.user_id, "email": instance.email}

    def login(self, dto: LoginRequest) -> LoginResponse:
        from api._security import create_access_token

        user = self.repo.get_by_email(dto.email)
        if not user or not _verify_password(dto.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        profile = _fetch_user_profile(user.user_id)

        if not profile.get("isActive", profile.get("is_active", True)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been suspended.",
            )

        role = profile.get("role", "")
        patient_id = profile.get("patientId") or profile.get("patient_id")
        provider_id = profile.get("providerId") or profile.get("provider_id")

        token = create_access_token(
            user.user_id,
            role,
            email=user.email,
            patient_id=patient_id,
            provider_id=provider_id,
        )
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            role=role,
            must_change_password=user.must_change_password,
            patient_id=patient_id,
            provider_id=provider_id,
            email=user.email,
        )

    def set_password(self, dto: SetPasswordRequest) -> dict:
        payload = _decode_reset_token(dto.token)
        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
        user = self.repo.get_by_id(user_id)
        if not user or user.email != payload.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
        self.repo.update_password(user, _hash_password(dto.new_password))
        return {"success": True}

    def forgot_password(self, email: str) -> dict:
        user = self.repo.get_by_email(email)
        if user:
            token = _create_reset_token(user.user_id, user.email)
            _send_password_link_email(user.email, token, is_invite=False)
        return {
            "success": True,
            "message": (
                "If an account exists for that email, a password reset link "
                "has been sent. The link expires in 10 minutes."
            ),
        }

    def me(self, jwt_user: dict) -> CurrentUserResponse:
        user_id = jwt_user.get("user_id")
        user = self.repo.get_by_id(int(user_id)) if user_id else None
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        profile = _fetch_user_profile(user.user_id)
        role = profile.get("role", "")
        patient_id = profile.get("patientId") or profile.get("patient_id")
        provider_id = profile.get("providerId") or profile.get("provider_id")

        return CurrentUserResponse(
            email=user.email,
            role=role,
            must_change_password=user.must_change_password,
            patient_id=patient_id,
            provider_id=provider_id,
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
        from messaging import publish_event_nowait, EventAction

        if self.repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An auth account with this email already exists",
            )
        instance = self.repo.create(
            email=email,
            password_hash=_unusable_password_hash(),
            must_change_password=True,
        )
        token = _create_reset_token(instance.user_id, email)

        publish_event_nowait(
            "user",
            EventAction.CREATED,
            extra={
                "user_id": instance.user_id,
                "email": email,
                "role": role.value if isinstance(role, UserRole) else str(role),
                "patient_id": patient_id,
                "provider_id": provider_id,
                "invite_token": token,
            },
        )
        return instance
