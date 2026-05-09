"""Lightweight base for consuming clinical events.

Use this as a starting point for downstream services. Subclass `Consumer`,
override `handle_message`, and the runner will declare a durable queue,
bind it to the topic exchange, and dispatch messages.

Example::

    class MyConsumer(Consumer):
        queue_name = "my.service"
        binding_keys = ("encounter.*", "condition.*")

        async def handle_message(self, payload, routing_key):
            print(routing_key, payload)

    asyncio.run(MyConsumer().run())
"""
from __future__ import annotations

import asyncio
import json
import logging
import signal
from typing import Any, Iterable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from .config import rabbitmq_url
from .events import EXCHANGE_NAME

logger = logging.getLogger(__name__)


class Consumer:
    queue_name: str = "clinical.events.default"
    binding_keys: Iterable[str] = ("#",)
    prefetch: int = 16

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        """Override. By default, log + ack."""
        logger.info("[%s] %s", routing_key, payload)

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode("utf-8"))
            except Exception:
                logger.exception("Bad message body, dropping")
                return
            await self.handle_message(payload, message.routing_key or "")

    async def run(self) -> None:
        from .config import RECONNECT_INTERVAL_SECONDS
        url = rabbitmq_url()
        while True:
            try:
                connection = await aio_pika.connect_robust(url)
                break
            except Exception:
                logger.warning("RabbitMQ not ready, retrying in %ss", RECONNECT_INTERVAL_SECONDS)
                await asyncio.sleep(RECONNECT_INTERVAL_SECONDS)
        try:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=self.prefetch)
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(self.queue_name, durable=True)
            for key in self.binding_keys:
                await queue.bind(exchange, routing_key=key)

            logger.info(
                "Consuming queue=%s bindings=%s exchange=%s",
                self.queue_name, list(self.binding_keys), EXCHANGE_NAME,
            )

            stop = asyncio.Event()
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, stop.set)
                except NotImplementedError:
                    # Windows doesn't support add_signal_handler for SIGTERM
                    pass

            await queue.consume(self._on_message)
            await stop.wait()
        finally:
            await connection.close()
