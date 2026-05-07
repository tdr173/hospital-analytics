from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class EncounterModel(SQLModel, table=True):
    __tablename__ = "encounter"
    __table_args__ = {"extend_existing": True}

    encounter_id: str = Field(primary_key=True)

    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    organization_id: str = Field(foreign_key="organization.organization_id", index=True)
    provider_id: str = Field(foreign_key="provider.provider_id", index=True)

    start_date: datetime
    end_date: datetime
    duration: float = Field(default=0.0)

    encounter_class: str = Field(index=True)
    description: str
    reason_description: Optional[str] = None

