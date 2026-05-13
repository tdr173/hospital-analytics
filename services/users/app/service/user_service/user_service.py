from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from api._scope import Scope

from fastapi import HTTPException
from starlette import status

from domain.models.user_profile_model import UserProfile
from domain.schemas.user_schemas.user_schema import (
    UserProfileResponse,
    UserProfileUpdate,
    UserListResponse,
)
from repository.user_repository import UserRepository


def _to_response(p: UserProfile) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=p.user_id,
        email=p.email,
        role=p.role.value if hasattr(p.role, "value") else str(p.role),
        patient_id=p.patient_id,
        provider_id=p.provider_id,
        display_name=p.display_name,
        phone=p.phone,
        job_title=p.job_title,
        is_active=p.is_active,
        created_at=p.created_at,
    )


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_profile_internal(self, user_id: int) -> UserProfileResponse:
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User profile not found")
        return _to_response(profile)

    def list_users(self, page: int, rows: int) -> UserListResponse:
        items, total = self.repo.list_all(page=page, rows=rows)
        return UserListResponse(items=[_to_response(p) for p in items], total=total)

    def get_user(self, scope: "Scope", user_id: int) -> UserProfileResponse:
        requester_id = int(scope.user_id) if scope.user_id else None
        if not scope.is_manager and requester_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return _to_response(profile)

    def update_user(self, scope: "Scope", user_id: int, dto: UserProfileUpdate) -> UserProfileResponse:
        requester_id = int(scope.user_id) if scope.user_id else None
        if not scope.is_manager and requester_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
        if dto.is_active is not None and not scope.is_manager:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only managers can change account status")
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        updates = dto.model_dump(exclude_none=True)
        profile = self.repo.update(profile, **updates)
        return _to_response(profile)

    def delete_user(self, user_id: int) -> None:
        from messaging import publish_event_nowait, EventAction
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        self.repo.delete_by_user_id(user_id)
        publish_event_nowait(
            "user",
            EventAction.DELETED,
            extra={"user_id": user_id},
        )
