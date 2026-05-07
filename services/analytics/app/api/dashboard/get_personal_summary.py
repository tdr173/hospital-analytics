from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from repository import PatientRepository
from service.llm_prompts import personal_summary
from .dashboard_router import dashboard_router


@dashboard_router.get("/personal-summary")
async def get_personal_summary(
    patientId: str = Query(...),
    db: Session = Depends(get_db),
):
    repo = PatientRepository(db)
    try:
        patient = repo.get_patient(patientId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    summary = repo.get_patient_summary(patientId)
    conditions = repo.get_patient_conditions(patientId)
    medications = repo.get_patient_medications(patientId)
    encounters = repo.get_patient_encounters(patientId)

    data = {
        "name": f"{patient.first_name} {patient.last_name}",
        "age": patient.age,
        "gender": patient.gender,
        "summary": (
            summary.model_dump() if hasattr(summary, "model_dump")
            else summary.dict() if hasattr(summary, "dict")
            else summary.__dict__
        ),
        "active_conditions": [
            c.description for c in conditions if c.end_date is None
        ][:10],
        "current_medications": [
            m.description for m in medications if m.end_date is None
        ][:10],
        "recent_encounters": [
            {
                "date": str(e.start_date),
                "class": e.encounter_class,
                "description": e.description,
            }
            for e in encounters[:5]
        ],
    }
    return {"markdown": personal_summary(data)}
