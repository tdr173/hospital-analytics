from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class MedicationModel(SQLModel, table=True):
    __tablename__ = "medication"

    id: int = Field(default=None, primary_key=True)

    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    encounter_id: str = Field(foreign_key="encounter.encounter_id", index=True)

    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: float = Field(default=0.0)

    medication_code: str = Field(index=True)
    description: str = Field(index=True)
    reason_description: Optional[str] = None