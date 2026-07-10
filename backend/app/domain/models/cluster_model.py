from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ClusterModel(SQLModel, table=True):
    __tablename__ = "cluster"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    cluster_label: int = Field(index=True)   # -1 marks outliers

    created_at: datetime = Field(default_factory=datetime.now)

    color: str = Field(default="#006780")
    title: str
    description: str
    insight: str
    recommendation: str
    ai_analysis: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    detail_cache: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
