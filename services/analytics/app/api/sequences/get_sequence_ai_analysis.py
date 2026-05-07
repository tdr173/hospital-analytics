from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import SequenceService
from domain import SequenceAiAnalysisResponse
from repository import SequenceRepository
from api._scope import Scope, scope_dep, require_manager
from .sequence_router import sequence_router


@sequence_router.get("/ai-analysis/{pattern_id}", response_model=SequenceAiAnalysisResponse)
async def get_sequence_ai_analysis(
    pattern_id: int,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    require_manager(scope)
    repo = SequenceRepository(db)
    service = SequenceService(repo)

    try:
        return service.get_ai_analysis(pattern_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
