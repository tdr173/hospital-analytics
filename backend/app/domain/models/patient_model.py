from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field


class PatientModel(SQLModel, table=True):
    __tablename__ = "patient"

    patient_id: int = Field(primary_key=True)
    birthdate: Optional[date]
    deathdate: Optional[date]

    first_name: str = Field(index=True, nullable=False, max_length=50)
    last_name: str = Field(index=True, nullable=False, max_length=50)

    marital: Optional[str]
    race: Optional[str]
    ethnicity: Optional[str]
    gender: Optional[str]
    city: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]