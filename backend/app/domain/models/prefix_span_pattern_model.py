from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class PrefixSpanPatternModel(SQLModel, table=True):
    __tablename__ = "prefix_span_pattern"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    rank: int
    pattern_str: str
    length: int
    support_count: int
    support_pct: float
    ai_analysis: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    cluster_label: Optional[int] = Field(default=None, index=True)
