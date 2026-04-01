from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ClusterPatientModel(SQLModel, table=True):
    __tablename__ = "cluster_patient"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    run_id: int = Field(foreign_key="cluster_run.id", index=True)
    patient_id: str = Field(index=True)

    cluster_label: int              # 0, 1, 2, ... or -1 for outliers
    is_outlier: bool = Field(default=False)

    pca_x: Optional[float] = Field(default=None)
    pca_y: Optional[float] = Field(default=None)

    features: dict = Field(sa_column=Column(JSONB))   # all numerical + categorical features, dynamic
