from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from repository._helpers.names import patient_name_col, provider_name_col

__all__ = [
    "patient_name_col",
    "provider_name_col",
    "MAX_PAGE_SIZE",
    "clamp_page_size",
    "link_patient_provider",
]

MAX_PAGE_SIZE = 200


def clamp_page_size(rows: int) -> int:
    """Defence against clients requesting absurdly large pages (OOM risk)."""
    if rows is None or rows < 1:
        return 1
    return min(rows, MAX_PAGE_SIZE)


def link_patient_provider(db: Session, patient_id: str, provider_id: str) -> None:
    """Idempotently add a (patient_id, provider_id) row to the patient_provider
    junction table so the patient shows up in that provider's panel.

    Relies on the table's unique (patient_id, provider_id) constraint via
    ON CONFLICT DO NOTHING, so it is safe to call on every create/update.
    """
    # imported here to avoid a circular import at module load time
    from domain import PatientProviderModel

    if not patient_id or not provider_id:
        return
    stmt = (
        pg_insert(PatientProviderModel.__table__)
        .values(patient_id=patient_id, provider_id=provider_id)
        .on_conflict_do_nothing(index_elements=["patient_id", "provider_id"])
    )
    db.execute(stmt)
    db.commit()
