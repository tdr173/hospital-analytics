from fastapi import Depends, Query
from api._scope import DEFAULT_PROVIDER_ID
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import EncounterModel, ConditionModel
from service.llm_prompts import practice_summary
from .dashboard_router import dashboard_router


@dashboard_router.get("/practice-summary")
async def get_practice_summary(
    providerId: str = Query(DEFAULT_PROVIDER_ID),
    db: Session = Depends(get_db),
):
    panel_size = (
        db.query(func.count(func.distinct(EncounterModel.patient_id)))
        .filter(EncounterModel.provider_id == providerId)
        .scalar()
        or 0
    )
    total_encounters = (
        db.query(func.count(EncounterModel.encounter_id))
        .filter(EncounterModel.provider_id == providerId)
        .scalar()
        or 0
    )

    top_conditions_rows = db.execute(
        text(
            """
            SELECT c.description, COUNT(DISTINCT c.patient_id) AS cnt
            FROM condition c
            WHERE c.patient_id IN (
                SELECT DISTINCT patient_id FROM encounter WHERE provider_id = :pid
            )
            GROUP BY c.description
            ORDER BY cnt DESC
            LIMIT 5
            """
        ),
        {"pid": providerId},
    ).fetchall()

    top_classes_rows = (
        db.query(EncounterModel.encounter_class, func.count(EncounterModel.encounter_id).label("cnt"))
        .filter(EncounterModel.provider_id == providerId)
        .group_by(EncounterModel.encounter_class)
        .order_by(func.count(EncounterModel.encounter_id).desc())
        .limit(5)
        .all()
    )

    data = {
        "panel_size": panel_size,
        "total_encounters": total_encounters,
        "top_conditions": [{"description": r[0], "patients": r[1]} for r in top_conditions_rows],
        "top_encounter_classes": [{"class": r[0], "count": r[1]} for r in top_classes_rows],
    }
    return {"markdown": practice_summary(data)}
