"""JWT issuance + Bearer-token verification.

Mirrors the reference auth_service/utils/security.py pattern, adapted to
the hospital-analytics monolith.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status


SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


# tokenUrl is the path the FE hits to acquire a token. Used by the OpenAPI
# docs for the "Authorize" button - real auth happens via Authorization headers.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_access_token(
    user_id: int,
    role: str,
    *,
    email: Optional[str] = None,
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    expire_minutes: Optional[int] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes if expire_minutes is not None else JWT_EXPIRE_MINUTES
    )
    payload: dict = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    if email:
        payload["email"] = email
    if patient_id:
        payload["patient_id"] = patient_id
    if provider_id:
        payload["provider_id"] = provider_id
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Strict dependency: 401 if no token / invalid token."""
    payload = decode_token(token)
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role"),
        "email": payload.get("email"),
        "patient_id": payload.get("patient_id"),
        "provider_id": payload.get("provider_id"),
    }


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[dict]:
    """Soft dependency: returns None if no token. For routes that support
    both legacy query-scope auth and JWT during the migration."""
    if not token:
        return None
    payload = decode_token(token)
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role"),
        "email": payload.get("email"),
        "patient_id": payload.get("patient_id"),
        "provider_id": payload.get("provider_id"),
    }


def require_role(*roles: str):
    def _wrapper(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
        return user
    return _wrapper
