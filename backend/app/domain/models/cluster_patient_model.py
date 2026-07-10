from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ClusterPatientModel(SQLModel, table=True):
    __tablename__ = "cluster_patient"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    patient_id: str = Field(index=True, foreign_key="patient.patient_id")

    cluster_label: int = Field(index=True)   # -1 marks outliers
    is_outlier: bool = Field(default=False)

    pca_x: Optional[float] = Field(default=None)
    pca_y: Optional[float] = Field(default=None)

    features: dict = Field(sa_column=Column(JSONB))   # feature keys vary by clustering run
