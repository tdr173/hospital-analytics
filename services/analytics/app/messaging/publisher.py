"""Fire-and-forget publish helper.

Two entry points:
  * `publish_event` - awaitable; for code paths that are already async.
  * `publish_event_nowait` - schedules the publish on the running loop and
    returns immediately. Use this from sync code or when you don't want to
    block the response.

Both swallow broker errors so a degraded RabbitMQ never breaks request
handling - they log and move on.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aio_pika

from .config import PUBLISH_TIMEOUT_SECONDS
from .connection import get_exchange
from .events import EventAction, build_payload, routing_key

logger = logging.getLogger(__name__)


async def publish_event(
    entity: str,
    action: EventAction,
    *,
    patient_id: str | None = None,
    encounter_id: str | None = None,
    record_id: int | str | None = None,
    extra: dict[str, Any] | None = None,
) -> bool:
    """Publish a single event. Returns True on publish, False if dropped."""
    exchange = get_exchange()
    if exchange is None:
        logger.debug("publish_event noop (no broker): %s.%s", entity, action.value)
        return False

    payload = build_payload(
        entity, action,
        patient_id=patient_id,
        encounter_id=encounter_id,
        record_id=record_id,
        extra=extra,
    )
    body = json.dumps(payload, default=str).encode("utf-8")
    message = aio_pika.Message(
        body=body,
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    rk = routing_key(entity, action)
    try:
        await asyncio.wait_for(
            exchange.publish(message, routing_key=rk),
            timeout=PUBLISH_TIMEOUT_SECONDS,
        )
        return True
    except Exception:
        logger.warning("publish_event failed: %s", rk, exc_info=False)
        return False


def publish_event_nowait(
    entity: str,
    action: EventAction,
    *,
    patient_id: str | None = None,
    encounter_id: str | None = None,
    record_id: int | str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Schedule a publish on the running loop without awaiting.

    Safe to call from async route handlers when you want zero added latency
    on the response path. If there is no running loop (sync context with
    no executor), the publish is dropped with a debug log.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.debug("publish_event_nowait dropped (no running loop): %s.%s", entity, action.value)
        return
    loop.create_task(publish_event(
        entity, action,
        patient_id=patient_id,
        encounter_id=encounter_id,
        record_id=record_id,
        extra=extra,
    ))
