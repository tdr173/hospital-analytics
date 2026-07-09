from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import PipelineService
from repository import PipelineRepository
from domain import PipelineStatus
from .pipeline_router import pipeline_router


@pipeline_router.post("/run", response_model=PipelineStatus)
def run_pipeline(db: Session = Depends(get_db)):
    service = PipelineService(PipelineRepository(db))
    started, status = service.start_manual()
    if not started:
        raise HTTPException(status_code=409, detail="Pipeline is already running")
    return status
