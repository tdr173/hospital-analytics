"""Request scoping (role + patient_id + provider_id).

Two ways to populate Scope, in this order:

1. **JWT (preferred).** If the request carries `Authorization: Bearer <jwt>`,
   `role` / `patient_id` / `provider_id` are read from the token claims.
2. **Query params (legacy).** Falls back to `?role=&patientId=&providerId=`
   for the demo/dev path that doesn't yet authenticate. Once every caller
   sends a Bearer token, the legacy branch is dead and can be deleted.

Tokens are validated against the same SECRET_KEY each service is configured
with. An invalid/expired Bearer token is treated as "no token" rather than
401, so an FE that holds a stale token but is hitting a non-protected route
still gets through with anonymous (manager-default) scope.
"""
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Query, Request

from ._security import decode_token


@dataclass
class Scope:
    role: Optional[str] = None
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    user_id: Optional[str] = None

    @property
    def is_manager(self) -> bool:
        return self.role is None or self.role.upper() == "MANAGER"

    @property
    def is_doctor(self) -> bool:
        return self.role is not None and self.role.upper() == "DOCTOR"

    @property
    def is_patient(self) -> bool:
        return self.role is not None and self.role.upper() == "PATIENT"


DEFAULT_PROVIDER_ID = "21ac7fa4-a452-3556-b812-f84c92369a6c"


def _scope_from_jwt(request: Request) -> Optional[Scope]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
    except HTTPException:
        # Invalid/expired token -> let query-param fallback handle it.
        return None
    return Scope(
        role=payload.get("role"),
        patient_id=payload.get("patient_id"),
        provider_id=payload.get("provider_id"),
        user_id=payload.get("sub"),
    )


def scope_dep(
    request: Request,
    role: Optional[str] = Query(None),
    patientId: Optional[str] = Query(None),
    providerId: Optional[str] = Query(None),
) -> Scope:
    jwt_scope = _scope_from_jwt(request)
    if jwt_scope is not None:
        # Apply doctor default when JWT lacks an explicit provider_id.
        if jwt_scope.is_doctor and not jwt_scope.provider_id:
            jwt_scope.provider_id = DEFAULT_PROVIDER_ID
        return jwt_scope
    return Scope(
        role=role,
        patient_id=patientId,
        provider_id=providerId or DEFAULT_PROVIDER_ID,
    )


def require_manager(scope: Scope) -> None:
    if not scope.is_manager:
        raise HTTPException(status_code=403, detail="Manager-only endpoint")


def require_doctor(scope: Scope) -> None:
    if not scope.is_doctor:
        raise HTTPException(status_code=403, detail="Doctor-only endpoint")


def require_patient_access(scope: Scope, target_patient_id: str) -> None:
    if scope.is_patient and scope.patient_id and scope.patient_id != target_patient_id:
        raise HTTPException(
            status_code=403, detail="Patient may only access their own record"
        )


def require_provider_access(scope: Scope, target_provider_id: str) -> None:
    if scope.is_doctor and scope.provider_id and scope.provider_id != target_provider_id:
        raise HTTPException(
            status_code=403, detail="Doctor may only access their own profile"
        )
