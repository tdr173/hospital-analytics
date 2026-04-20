from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Query


@dataclass
class Scope:
    role: Optional[str] = None
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None

    @property
    def is_manager(self) -> bool:
        return self.role is None or self.role.upper() == "MANAGER"

    @property
    def is_doctor(self) -> bool:
        return self.role is not None and self.role.upper() == "DOCTOR"

    @property
    def is_patient(self) -> bool:
        return self.role is not None and self.role.upper() == "PATIENT"


def scope_dep(
    role: Optional[str] = Query(None),
    patientId: Optional[str] = Query(None),
    providerId: Optional[str] = Query(None),
) -> Scope:
    return Scope(role=role, patient_id=patientId, provider_id=providerId)


def require_manager(scope: Scope) -> None:
    if not scope.is_manager:
        raise HTTPException(status_code=403, detail="Manager-only endpoint")


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
