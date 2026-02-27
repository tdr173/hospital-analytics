from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ObservationModel(SQLModel, table=True):
    __tablename__ = "observation"

    id: int = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    encounter_id: Optional[str] = Field(foreign_key="encounter.encounter_id", index=True)

    date: datetime
    observation_code: str = Field(index=True)
    description: str

    value: str
    value_numeric: Optional[float] = None
    units: Optional[str] = None