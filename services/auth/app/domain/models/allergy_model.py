from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field


class AllergyModel(SQLModel, table=True):
    __tablename__ = "allergy"

    id: int = Field(default=None, primary_key=True)

    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    encounter_id: Optional[str] = Field(foreign_key="encounter.encounter_id", default=None)

    start_date: date
    end_date: Optional[date] = None

    allergy_code: str = Field(index=True)
    description: str = Field(index=True)