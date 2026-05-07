"""RabbitMQ connection lifecycle.

The app shouldn't break when the broker is unreachable. The publisher
treats a missing connection as a no-op (with a warning log), so dev
environments without docker-compose still work.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractRobustExchange

from .config import rabbitmq_url
from .events import EXCHANGE_NAME

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 10
_RETRY_BASE_DELAY = 2.0   # seconds; doubles each attempt up to _RETRY_MAX_DELAY
_RETRY_MAX_DELAY = 30.0


class _State:
    connection: Optional[AbstractRobustConnection] = None
    channel: Optional[AbstractRobustChannel] = None
    exchange: Optional[AbstractRobustExchange] = None


_state = _State()


def get_exchange() -> Optional[AbstractRobustExchange]:
    """Return the publish exchange, or None if messaging is degraded."""
    return _state.exchange


async def startup_messaging() -> None:
    """Connect to RabbitMQ and declare the topic exchange.

    Retries with exponential backoff so that slow broker startup (common in
    docker-compose) doesn't permanently disable messaging. If all attempts
    fail, the app keeps running with publishing disabled.
    """
    url = rabbitmq_url()
    delay = _RETRY_BASE_DELAY
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            _state.connection = await aio_pika.connect_robust(url)
            _state.channel = await _state.connection.channel()
            _state.exchange = await _state.channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            logger.info("RabbitMQ connected at %s, exchange=%s", url, EXCHANGE_NAME)
            return
        except Exception as exc:
            _state.connection = None
            _state.channel = None
            _state.exchange = None
            if attempt == _RETRY_ATTEMPTS:
                logger.warning(
                    "RabbitMQ unavailable at %s after %d attempts - messaging will be a no-op until restart",
                    url,
                    _RETRY_ATTEMPTS,
                )
                return
            logger.info(
                "RabbitMQ not ready (attempt %d/%d): %s — retrying in %.0fs",
                attempt,
                _RETRY_ATTEMPTS,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, _RETRY_MAX_DELAY)


async def shutdown_messaging() -> None:
    """Close the channel + connection cleanly. Tolerate already-closed state."""
    try:
        if _state.channel is not None and not _state.channel.is_closed:
            await _state.channel.close()
    except Exception:
        logger.debug("Error closing RabbitMQ channel", exc_info=True)
    try:
        if _state.connection is not None and not _state.connection.is_closed:
            await _state.connection.close()
    except Exception:
        logger.debug("Error closing RabbitMQ connection", exc_info=True)
    _state.exchange = None
    _state.channel = None
    _state.connection = None
