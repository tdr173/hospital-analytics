from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class ConditionModel(SQLModel, table=True):
    __tablename__ = "condition"

    id: int = Field(default=None, primary_key=True)

    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    encounter_id: str = Field(foreign_key="encounter.encounter_id", index=True)

    start_date: datetime
    end_date: Optional[datetime] = None

    condition_code: str = Field(index=True)
    description: str