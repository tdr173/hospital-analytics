from typing import Optional
from sqlmodel import SQLModel, Field


class OrganizationModel(SQLModel, table=True):
    __tablename__ = "organization"

    organization_id: str = Field(primary_key=True)

    name: str = Field(index=True, nullable=False)
    city: Optional[str] = None
    phone: Optional[str] = None
    utilization: int = Field(default=0)