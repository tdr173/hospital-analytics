from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ClusterModel(SQLModel, table=True):
    __tablename__ = "cluster"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    cluster_label: int = Field(index=True)   # 0, 1, 2 or -1 for outliers

    color: str = Field(default="#006780")
    title: str
    description: str
    insight: str
    recommendation: str
    ai_analysis: Optional[dict] = Field(default=None, sa_column=Column(JSONB))  # cached per-cluster AI analysis
