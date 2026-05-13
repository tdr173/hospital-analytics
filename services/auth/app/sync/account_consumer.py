"""auth service consumers for clinical + user lifecycle events.

AccountSyncConsumer — listens to clinical-core events to provision credentials:
  patient.created  → create auth_user + publish user.created (users-service creates profile)
  provider.created → create auth_user + publish user.created
  patient.deleted  → delete auth_user
  provider.deleted → delete auth_user

UserDeletedConsumer — listens to users-service deletion events:
  user.deleted     → delete auth_user by user_id
"""
from __future__ import annotations

import logging
from typing import Any

from db.db_connector import SessionLocal
from messaging.consumer import Consumer
from messaging.events import EventAction

logger = logging.getLogger(__name__)


class AccountSyncConsumer(Consumer):
    queue_name = "auth.account_sync"
    binding_keys = (
        "patient.created", "patient.deleted",
        "provider.created", "provider.deleted",
    )

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        from repository import AuthRepository
        from service import AuthService
        from domain import UserRole

        entity = payload.get("entity")
        action = payload.get("action")
        email = payload.get("email") or payload.get("extra", {}).get("email")
        patient_id = payload.get("patient_id")
        provider_id = payload.get("provider_id") or payload.get("extra", {}).get("provider_id")

        if action == EventAction.CREATED.value and email:
            db = SessionLocal()
            try:
                svc = AuthService(AuthRepository(db))
                if entity == "patient" and patient_id:
                    svc.create_account_for_patient(email=email, patient_id=patient_id)
                    logger.info("provisioned PATIENT account for %s", email)
                elif entity == "provider" and provider_id:
                    svc.create_account_for_provider(
                        email=email, provider_id=provider_id, role=UserRole.DOCTOR
                    )
                    logger.info("provisioned DOCTOR account for %s", email)
            except Exception:
                logger.exception("account provisioning failed for %s", email)
            finally:
                db.close()
            return

        if action == EventAction.DELETED.value:
            db = SessionLocal()
            try:
                from repository import AuthRepository
                repo = AuthRepository(db)
                # Look up by email if provided (patient/provider deleted events carry patient_id/provider_id,
                # not user_id — we no longer store those on auth_user, so we can only match by email if present)
                target_email = email or payload.get("extra", {}).get("email")
                if target_email:
                    target = repo.get_by_email(target_email)
                    if target:
                        repo.delete(target)
                        logger.info("deleted auth account for %s", target_email)
            except Exception:
                logger.exception("auth account deletion failed for %s", routing_key)
            finally:
                db.close()


class UserDeletedConsumer(Consumer):
    """Listens for user.deleted events published by users-service when an admin deletes a user."""
    queue_name = "auth.user_deleted"
    binding_keys = ("user.deleted",)

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        user_id = payload.get("user_id") or payload.get("extra", {}).get("user_id")
        if not user_id:
            logger.warning("user.deleted event missing user_id: %s", payload)
            return
        db = SessionLocal()
        try:
            from repository import AuthRepository
            repo = AuthRepository(db)
            repo.delete_by_id(int(user_id))
            logger.info("deleted auth_user for user_id=%s", user_id)
        except Exception:
            logger.exception("failed to delete auth_user for user_id=%s", user_id)
        finally:
            db.close()
