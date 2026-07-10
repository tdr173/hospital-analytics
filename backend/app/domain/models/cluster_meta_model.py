from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


class ClusterMetaModel(SQLModel, table=True):
    """Singleton table (one row, id=1) holding metadata for the current clustering run. Re-run truncates and re-inserts."""
    __tablename__ = "cluster_meta"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    algorithm: str
    n_clusters: int
    n_patients: int
    n_outliers: int = Field(default=0)
    numerical_features: list = Field(sa_column=Column(JSONB))
    categorical_features: list = Field(sa_column=Column(JSONB))
    params: dict = Field(sa_column=Column(JSONB))
    metrics: dict = Field(sa_column=Column(JSONB))
    heatmap: Optional[bytes] = Field(default=None)
    pca_image: Optional[bytes] = Field(default=None)
    ai_analysis: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
