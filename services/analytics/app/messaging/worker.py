"""Default firehose worker that just logs every clinical event.

Run from `backend/app/`::

    python -m messaging.worker

This is a placeholder consumer to prove the pipe end-to-end. Real
downstream services (later split into microservices) should subclass
`Consumer` and bind to the specific routing keys they care about.
"""
from __future__ import annotations

import asyncio
import logging

from .consumer import Consumer


class FirehoseConsumer(Consumer):
    queue_name = "clinical.events.firehose"
    binding_keys = ("#",)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(FirehoseConsumer().run())


if __name__ == "__main__":
    main()
