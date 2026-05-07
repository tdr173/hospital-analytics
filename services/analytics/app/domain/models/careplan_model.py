from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class CarePlanModel(SQLModel, table=True):
    __tablename__ = "careplan"

    id: int = Field(default=None, primary_key=True)

    patient_id: str = Field(index=True)
    encounter_id: str = Field(index=True)

    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None

    careplan_code: str = Field(index=True)
    description: str = Field(index=True)
    reason_code: Optional[str] = None
    reason_description: Optional[str] = None
