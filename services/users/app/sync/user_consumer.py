"""users-service consumer: manages user profiles in response to events.

Bindings:
  user.created     -> create user_profile from auth-service registration event
  patient.deleted  -> delete user_profile linked to that patient_id
  provider.deleted -> delete user_profile linked to that provider_id
"""
from __future__ import annotations

import logging
from typing import Any

from db.db_connector import SessionLocal
from messaging.consumer import Consumer

logger = logging.getLogger(__name__)


class UserSyncConsumer(Consumer):
    queue_name = "users.profile_sync"
    binding_keys = (
        "user.created",
        "patient.deleted",
        "provider.deleted",
    )

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        from repository import UserRepository

        if routing_key == "user.created":
            db = SessionLocal()
            try:
                repo = UserRepository(db)
                repo.create(
                    user_id=payload["user_id"],
                    email=payload["email"],
                    role=payload["role"],
                    patient_id=payload.get("patient_id"),
                    provider_id=payload.get("provider_id"),
                    display_name=payload.get("display_name"),
                    phone=payload.get("phone"),
                    job_title=payload.get("job_title"),
                )
                logger.info("created user_profile for user_id=%s", payload.get("user_id"))
            except Exception:
                logger.exception("user_profile creation failed for %s", payload.get("email"))
            finally:
                db.close()
            return

        patient_id = payload.get("patient_id")
        provider_id = payload.get("provider_id") or payload.get("extra", {}).get("provider_id")

        if routing_key == "patient.deleted" and patient_id:
            db = SessionLocal()
            try:
                UserRepository(db).delete_by_patient_id(patient_id)
                logger.info("deleted user_profile for patient_id=%s", patient_id)
            except Exception:
                logger.exception("user_profile deletion failed for patient_id=%s", patient_id)
            finally:
                db.close()

        elif routing_key == "provider.deleted" and provider_id:
            db = SessionLocal()
            try:
                UserRepository(db).delete_by_provider_id(provider_id)
                logger.info("deleted user_profile for provider_id=%s", provider_id)
            except Exception:
                logger.exception("user_profile deletion failed for provider_id=%s", provider_id)
            finally:
                db.close()
