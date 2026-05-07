from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class PatientProviderModel(SQLModel, table=True):
    __tablename__ = "patient_provider"
    __table_args__ = (UniqueConstraint("patient_id", "provider_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.patient_id", index=True)
    provider_id: str = Field(foreign_key="provider.provider_id", index=True)
