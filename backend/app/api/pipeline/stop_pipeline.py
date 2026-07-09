from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import PipelineService
from repository import PipelineRepository
from domain import PipelineStatus
from .pipeline_router import pipeline_router


@pipeline_router.post("/stop", response_model=PipelineStatus)
def stop_pipeline(db: Session = Depends(get_db)):
    service = PipelineService(PipelineRepository(db))
    accepted, status = service.stop_manual()
    if not accepted:
        raise HTTPException(status_code=409, detail="Pipeline is not running")
    return status
