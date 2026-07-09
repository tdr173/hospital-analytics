from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class PipelineRunModel(SQLModel, table=True):
    """
    Singleton table - always exactly one row (id=1). Tracks the state of the
    offline analytics pipeline (ETL -> clustering -> sequence mining) so the
    manager page can show live status/stage and the last run.
    """
    __tablename__ = "pipeline_run"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=1, primary_key=True)
    # IDLE | RUNNING | SUCCESS | FAILED | STOPPED
    status: str = Field(default="IDLE")
    # ETL | CLUSTERING | SEQUENCES_GLOBAL | SEQUENCES_CLUSTERS | DONE (nullable when idle)
    current_stage: Optional[str] = Field(default=None)
    etl_skipped: bool = Field(default=False)
    # manual | scheduled
    triggered_by: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    last_run_at: Optional[datetime] = Field(default=None)
    error: Optional[str] = Field(default=None)
    # set while RUNNING to ask the orchestrator to stop at the next checkpoint
    stop_requested: bool = Field(default=False)
