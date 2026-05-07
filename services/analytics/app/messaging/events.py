from enum import Enum
from typing import Any


# Single topic exchange. Routing keys follow `<entity>.<action>` so that
# subscribers can bind with patterns like `encounter.*` or `*.deleted`
# or just `#` for the firehose.
EXCHANGE_NAME = "clinical.events"


class EventAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


def routing_key(entity: str, action: EventAction) -> str:
    """Build a routing key. Entity is e.g. 'encounter', 'condition', 'medication'."""
    return f"{entity}.{action.value}"


def build_payload(
    entity: str,
    action: EventAction,
    *,
    patient_id: str | None = None,
    encounter_id: str | None = None,
    record_id: int | str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "entity": entity,
        "action": action.value,
    }
    if patient_id is not None:
        payload["patient_id"] = patient_id
    if encounter_id is not None:
        payload["encounter_id"] = encounter_id
    if record_id is not None:
        payload["record_id"] = record_id
    if extra:
        payload.update(extra)
    return payload
