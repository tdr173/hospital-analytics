from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ClusterRunModel(SQLModel, table=True):
    __tablename__ = "cluster_run"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    algorithm: str
    n_clusters: int
    n_patients: int
    n_outliers: int = Field(default=0)

    numerical_features: list = Field(sa_column=Column(JSONB))
    categorical_features: list = Field(sa_column=Column(JSONB))
    params: dict = Field(sa_column=Column(JSONB))    # scaler, gamma, init, random_state, etc.
    metrics: dict = Field(sa_column=Column(JSONB))   # silhouette, calinski, davies_bouldin, gower_silhouette
    heatmap: Optional[bytes] = Field(default=None)
    ai_analysis: Optional[dict] = Field(default=None, sa_column=Column(JSONB))  # cached AI analysis
