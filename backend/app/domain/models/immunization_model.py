from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ImmunizationModel(SQLModel, table=True):
    __tablename__ = "immunization"

    id: Optional[int] = Field(default=None, primary_key=True)

    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    encounter_id: str = Field(foreign_key="encounter.encounter_id", index=True)

    date: datetime

    immunization_code: str = Field(index=True)
    description: str = Field(index=True)