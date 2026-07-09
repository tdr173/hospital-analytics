from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import PipelineService
from repository import PipelineRepository
from domain import PipelineStatus
from .pipeline_router import pipeline_router


@pipeline_router.get("/status", response_model=PipelineStatus)
def get_pipeline_status(db: Session = Depends(get_db)):
    service = PipelineService(PipelineRepository(db))
    return service.get_status()
