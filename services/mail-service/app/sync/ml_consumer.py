"""ml-batch consumer: invalidates cluster results when clinical state
changes meaningfully.

For now this is a stub that simply logs. A future implementation can
trigger reclustering or update cluster_patient rows when patients are
deleted. The cross-DB FK from cluster_patient.patient_id to clinical_db
was removed; this consumer is what keeps ml_db's cluster_patient rows
coherent with clinical_db's patient table.
"""
from __future__ import annotations

import logging
from typing import Any

from db.db_connector import SessionLocal
from messaging.consumer import Consumer

logger = logging.getLogger(__name__)


class MlSyncConsumer(Consumer):
    queue_name = "ml.clinical_sync"
    binding_keys = ("patient.deleted",)

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        patient_id = payload.get("patient_id")
        if not patient_id:
            return
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(
                text("DELETE FROM cluster_patient WHERE patient_id = :pid"),
                {"pid": patient_id},
            )
            db.commit()
            logger.info("removed cluster_patient rows for deleted patient_id=%s", patient_id)
        except Exception:
            db.rollback()
            logger.exception("ml sync delete failed for patient_id=%s", patient_id)
        finally:
            db.close()
