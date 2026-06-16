from typing import Literal
from fastapi import Depends, Query
from api._scope import DEFAULT_PROVIDER_ID
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterModel, ConditionModel
from repository.statistics_repository._common import compute_min_date
from service.llm_prompts import practice_summary
from .dashboard_router import dashboard_router

RANGE_LABELS = {
    "week": "the last week",
    "month": "the last month",
    "year": "the last year",
}


@dashboard_router.get("/practice-summary")
async def get_practice_summary(
    providerId: str = Query(DEFAULT_PROVIDER_ID),
    range: Literal["week", "month", "year"] = Query(default="month"),
    db: Session = Depends(get_db),
):
    enc_cutoff = compute_min_date(db, EncounterModel.start_date, range)
    cond_cutoff = compute_min_date(db, ConditionModel.start_date, range)

    panel_query = (
        db.query(func.count(func.distinct(EncounterModel.patient_id)))
        .filter(EncounterModel.provider_id == providerId)
    )
    if enc_cutoff is not None:
        panel_query = panel_query.filter(EncounterModel.start_date >= enc_cutoff)
    panel_size = panel_query.scalar() or 0

    enc_query = (
        db.query(func.count(EncounterModel.encounter_id))
        .filter(EncounterModel.provider_id == providerId)
    )
    if enc_cutoff is not None:
        enc_query = enc_query.filter(EncounterModel.start_date >= enc_cutoff)
    total_encounters = enc_query.scalar() or 0

    top_conditions_rows = db.execute(
        text(
            """
            SELECT c.description, COUNT(DISTINCT c.patient_id) AS cnt
            FROM condition c
            WHERE c.patient_id IN (
                SELECT DISTINCT patient_id FROM encounter
                WHERE provider_id = :pid
                  AND (:enc_cutoff IS NULL OR start_date >= :enc_cutoff)
            )
              AND (:cond_cutoff IS NULL OR c.start_date >= :cond_cutoff)
            GROUP BY c.description
            ORDER BY cnt DESC
            LIMIT 5
            """
        ),
        {"pid": providerId, "enc_cutoff": enc_cutoff, "cond_cutoff": cond_cutoff},
    ).fetchall()

    classes_query = (
        db.query(EncounterModel.encounter_class, func.count(EncounterModel.encounter_id).label("cnt"))
        .filter(EncounterModel.provider_id == providerId)
    )
    if enc_cutoff is not None:
        classes_query = classes_query.filter(EncounterModel.start_date >= enc_cutoff)
    top_classes_rows = (
        classes_query
        .group_by(EncounterModel.encounter_class)
        .order_by(func.count(EncounterModel.encounter_id).desc())
        .limit(5)
        .all()
    )

    data = {
        "period": RANGE_LABELS.get(range, "the last month"),
        "panel_size": panel_size,
        "total_encounters": total_encounters,
        "top_conditions": [{"description": r[0], "patients": r[1]} for r in top_conditions_rows],
        "top_encounter_classes": [{"class": r[0], "count": r[1]} for r in top_classes_rows],
    }
    return {"markdown": practice_summary(data)}
