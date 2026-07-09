from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service.lllm_sql_agent_service import run_agent
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router


class ChatMessage(BaseModel):
    role: str
    content: str


class AskAIRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


@statistics_router.post("/sql-agent")
def statistics_ask_ai(
    request: AskAIRequest,
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    if scope.is_patient and not scope.patient_id:
        raise HTTPException(status_code=403, detail="Patient scope requires a patient id")
    history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    return run_agent(
        db,
        request.question,
        history,
        role=scope.role,
        provider_id=scope.provider_id,
        patient_id=scope.patient_id,
    )
