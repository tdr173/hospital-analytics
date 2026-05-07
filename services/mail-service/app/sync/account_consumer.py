"""auth service consumer: provisions auth accounts in response to clinical
events emitted by clinical-core.

Bindings:
  patient.created  -> if payload contains `email`, invite a PATIENT account
  provider.created -> if payload contains `email`, invite a DOCTOR account
  patient.deleted  -> deactivate / delete the linked auth account
  provider.deleted -> deactivate / delete the linked auth account

The consumer runs as an asyncio Task inside the auth FastAPI process. It
acks every message; soft-fails (logging) on handler errors so a single
poisoned message can't block the queue.
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
        # Lazy imports keep this module importable even when SQLModel metadata
        # for clinical tables hasn't been initialized in this process.
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
                repo = AuthRepository(db)
                target = None
                if entity == "patient" and patient_id:
                    target = repo.get_by_patient_id(patient_id) if hasattr(repo, "get_by_patient_id") else None
                elif entity == "provider" and provider_id:
                    target = repo.get_by_provider_id(provider_id) if hasattr(repo, "get_by_provider_id") else None
                if target is not None and hasattr(repo, "delete"):
                    repo.delete(target)
                    logger.info("deleted auth account for %s.%s", entity, patient_id or provider_id)
            except Exception:
                logger.exception("auth account deletion failed for %s", routing_key)
            finally:
                db.close()
