"""mail-service consumer: sends transactional email in response to events.

Currently subscribes to nothing by default — the existing flows already
trigger mail synchronously via `mail_sender.send_mail`. This stub is here
so a future event-driven mail flow (e.g. encounter reminders, weekly
digests) can subclass `Consumer` and bind appropriate routing keys.

Run from inside the mail-service container::

    python -m sync.mail_consumer
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from messaging.consumer import Consumer

logger = logging.getLogger(__name__)


class MailConsumer(Consumer):
    queue_name = "mail.notifications"
    # Bind to a future "notifications.send" routing key. Until something
    # publishes to it, this consumer will sit idle.
    binding_keys = ("notification.send",)

    async def handle_message(self, payload: dict[str, Any], routing_key: str) -> None:
        from mail_sender import send_mail, MailSendError

        to = payload.get("to")
        subject = payload.get("subject", "(no subject)")
        body = payload.get("body", "")
        html = payload.get("html")
        if not to:
            logger.warning("notification.send missing 'to': %s", payload)
            return
        try:
            send_mail(to=to, subject=subject, body=body, html=html)
            logger.info("sent mail to %s subject=%s", to, subject)
        except MailSendError:
            logger.exception("send_mail failed for %s", to)


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    asyncio.run(MailConsumer().run())


if __name__ == "__main__":
    main()
