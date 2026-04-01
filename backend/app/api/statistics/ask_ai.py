from pydantic import BaseModel
from .statistics_router import *
from service.lllm_sql_agent_service import run_agent


class ChatMessage(BaseModel):
    role: str
    content: str


class AskAIRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


@statistics_router.post("/sql-agent")
async def statistics_ask_ai(request: AskAIRequest):
    history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    response = run_agent(request.question, history)
    return response
