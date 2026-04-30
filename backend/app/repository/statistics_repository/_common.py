from datetime import timedelta
from typing import Optional, List

from sqlalchemy import func, cast, Numeric
from sqlalchemy.orm import Session

_DELTAS = {
    "week": timedelta(days=7),
    "month": timedelta(days=30),
}


def compute_min_date(db: Session, date_col, range_str: str):
    """Return inclusive lower bound for the requested range, or None for `all`.

    Anchored on MAX(date_col) — the dataset spans a 100-year synthetic timeline
    so today-relative ranges would be empty.
    """
    delta = _DELTAS.get(range_str)
    if delta is None:
        return None
    max_date = db.query(func.max(date_col)).scalar()
    if max_date is None:
        return None
    return max_date - delta


def provider_patient_subq(db: Session, provider_id: str):
    from domain.models.encounter_model import EncounterModel
    return (
        db.query(EncounterModel.patient_id)
        .filter(EncounterModel.provider_id == provider_id)
        .distinct()
        .subquery()
    )


def with_percentage(rows, total):
    return [
        {
            "label": row.label,
            "count": row.count,
            "percentage": round(row.count * 100.0 / total, 2) if total else 0,
        }
        for row in rows
    ]


def per_patient_stats(db: Session, model, code_col, filters: Optional[List] = None):
    q = db.query(
        model.patient_id,
        func.count(code_col).label("cnt"),
    )
    for f in (filters or []):
        q = q.filter(f)
    subquery = q.group_by(model.patient_id).subquery()

    result = db.query(
        func.round(cast(func.avg(subquery.c.cnt), Numeric), 2).label("avg"),
        func.min(subquery.c.cnt).label("min"),
        func.max(subquery.c.cnt).label("max"),
    ).one()

    return {
        "avg": float(result.avg or 0),
        "min": result.min or 0,
        "max": result.max or 0,
    }
