from typing import Optional
from sqlmodel import SQLModel, Field


class ProviderModel(SQLModel, table=True):
    __tablename__ = "provider"

    provider_id: str = Field(primary_key=True)
    organization_id: str = Field(foreign_key="organization.organization_id")

    first_name: str = Field(index=True, nullable=False)
    last_name: str = Field(index=True, nullable=False)

    gender: Optional[str] = None
    speciality: Optional[str] = Field(index=True)
    city: Optional[str] = None

    latitude: float
    longitude: float
    utilization: int = Field(default=0)