from fastapi import Depends, Request
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import PipelineService
from repository import PipelineRepository
from domain import PipelineOverview
from .pipeline_router import pipeline_router


@pipeline_router.get("", response_model=PipelineOverview)
def get_pipeline_overview(request: Request, db: Session = Depends(get_db)):
    scheduler = getattr(request.app.state, "scheduler", None)
    service = PipelineService(PipelineRepository(db), scheduler=scheduler)
    return service.get_overview()
