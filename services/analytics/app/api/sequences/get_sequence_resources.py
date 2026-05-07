from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import SequenceService
from domain import SequenceResourcesResponse
from repository import SequenceRepository
from .sequence_router import sequence_router


@sequence_router.get("/resources", response_model=SequenceResourcesResponse)
async def get_sequence_resources(db: Session = Depends(get_db)):
    repo = SequenceRepository(db)
    service = SequenceService(repo)
    return service.get_resources()
