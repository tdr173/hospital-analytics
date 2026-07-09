from typing import Optional
from datetime import datetime
from domain.schemas.camel_model import CamelModel


class PipelineStatus(CamelModel):
    """Lightweight snapshot used for polling while the pipeline runs."""
    status: str                              # IDLE | RUNNING | SUCCESS | FAILED | STOPPED
    current_stage: Optional[str] = None      # ETL | CLUSTERING | SEQUENCES_GLOBAL | SEQUENCES_CLUSTERS | DONE
    etl_skipped: bool = False
    triggered_by: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    stop_requested: bool = False


class DataCounts(CamelModel):
    patients: int
    medications: int
    procedures: int
    careplans: int
    conditions: int


class PipelineOverview(PipelineStatus):
    """Full snapshot for the initial page load: status + stats + counts."""
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    interpreted_clusters: int = 0
    total_clusters: int = 0
    interpreted_sequences: int = 0
    total_sequences: int = 0
    counts: DataCounts
