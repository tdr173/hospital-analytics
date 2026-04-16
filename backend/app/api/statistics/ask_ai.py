from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service.lllm_sql_agent_service import run_agent
from .statistics_router import statistics_router


class ChatMessage(BaseModel):
    role: str
    content: str


class AskAIRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


@statistics_router.post("/sql-agent")
def statistics_ask_ai(request: AskAIRequest, db: Session = Depends(get_db)):
    history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    return run_agent(db, request.question, history)
