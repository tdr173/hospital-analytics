import re
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .llm_models import ask_ai
from db.db_connector import _db_retrieve
from db.db_data import DB_SCHEMA
from prompts.sql_agent import (
    PROMPT_TRANSLATE,
    PROMPT_MEDICAL_ANSWER,
    PROMPT_GENERATE_SQL,
    PROMPT_VALIDATE_SQL,
    PROMPT_RESULT,
    DOCTOR_SCOPE_CLAUSE,
    PATIENT_SCOPE_CLAUSE,
)

load_dotenv()

MAX_RETRIES = 3
MAX_RESULT_ROWS = 100
MAX_RESULT_CHARS = 3000
MAX_HISTORY_TURNS = 5

DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE
)


class AgentState(TypedDict):
    db: Any  # SQLAlchemy Session - passed through, never serialized
    user_prompt: str
    original_prompt: str  # raw user question, no injected scope
    chat_history: str
    scope_clause: str  # role-based scope restriction injected into SQL steps
    translated_prompt: str
    general_answer: str  # set when the question is medical but needs no DB query
    sql_query: str
    query_result: str
    error_message: str
    validation_status: str
    feedback: str
    retry_count: int


def extract_clean_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def is_select_only(sql: str) -> bool:
    cleaned = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().rstrip(";").strip()

    if not (cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH")):
        return False

    if DANGEROUS_KEYWORDS.search(cleaned):
        return False

    return True


def truncate_result(result: str) -> str:
    if len(result) > MAX_RESULT_CHARS:
        return result[:MAX_RESULT_CHARS] + f"\n... (truncated, showing first {MAX_RESULT_CHARS} characters)"
    return result


def format_chat_context(history: str) -> str:
    if not history:
        return ""
    return f"Conversation history (for context resolution only):\n{history}"


def process_input(state: AgentState):
    scope_prefix = state.get('scope_clause') or ""
    full_prompt = (scope_prefix + "\n\nUser question: " + state['user_prompt']) if scope_prefix else state['user_prompt']

    prompt = PROMPT_TRANSLATE.format(
        initial_prompt=full_prompt,
        db_schema=DB_SCHEMA,
        chat_context=format_chat_context(state.get('chat_history', ''))
    )
    result = ask_ai(prompt).strip()

    if result.startswith("MEDICAL_GENERAL:"):
        question = result[len("MEDICAL_GENERAL:"):].strip()
        return {"translated_prompt": question, "error_message": "MEDICAL_GENERAL"}

    if "NOT_MEDICAL" in result:
        return {"error_message": "NOT_MEDICAL"}

    return {
        "translated_prompt": result,
        "retry_count": 0,
        "feedback": ""
    }


def answer_general(state: AgentState):
    prompt = PROMPT_MEDICAL_ANSWER.format(
        question=state['translated_prompt'],
        chat_context=format_chat_context(state.get('chat_history', ''))
    )
    response = ask_ai(prompt)
    print(f"[SQL Agent] General medical answer returned.\n")
    return {"general_answer": response}


def generate_query(state: AgentState):
    retry_context = ""
    if state.get('feedback'):
        retry_context = (
            f"IMPORTANT - Your previous query failed. Here is what went wrong:\n"
            f"Previous SQL: {state.get('sql_query', 'N/A')}\n"
            f"Error/Feedback: {state['feedback']}\n"
            f"Fix the issue and generate a corrected query."
        )

    scope_clause = state.get('scope_clause') or ""
    if scope_clause:
        scope_clause = scope_clause + "\n\n"

    prompt = PROMPT_GENERATE_SQL.format(
        prompt=state['translated_prompt'],
        db_schema=DB_SCHEMA,
        scope_clause=scope_clause,
        retry_context=retry_context,
        max_rows=MAX_RESULT_ROWS,
    )

    raw_response = ask_ai(prompt)
    clean_sql = extract_clean_sql(raw_response)

    attempt = state.get("retry_count", 0) + 1
    print(f"\n[SQL Agent] Generated SQL (attempt {attempt}):\n{clean_sql}\n")

    return {"sql_query": clean_sql}


def validate_query(state: AgentState):
    sql = state['sql_query']

    if not is_select_only(sql):
        return {
            "validation_status": "INCORRECT",
            "feedback": f"Query contains forbidden statements. Only SELECT queries are allowed. Generated SQL was: {sql}",
            "retry_count": state["retry_count"] + 1
        }

    scope_clause = state.get('scope_clause') or ""

    prompt = PROMPT_VALIDATE_SQL.format(
        prompt=state['translated_prompt'],
        sql_query=sql,
        db_schema=DB_SCHEMA,
        scope_clause=scope_clause,
    )

    response = ask_ai(prompt)

    if response.strip().upper().startswith("YES"):
        print(f"[SQL Agent] Validation: PASSED\n")
        return {"validation_status": "CORRECT", "feedback": ""}
    else:
        lines = response.split('\n')
        feedback = lines[1] if len(lines) > 1 else response
        print(f"[SQL Agent] Validation: FAILED - {feedback}\n")
        return {
            "validation_status": "INCORRECT",
            "feedback": f"Validation rejected the SQL: {feedback}. The query was: {sql}",
            "retry_count": state["retry_count"] + 1
        }


def execute_query(state: AgentState):
    try:
        result = _db_retrieve(state['db'], state['sql_query'])
        result_str = truncate_result(str(result))
        print(f"[SQL Agent] Execution: OK - {len(result)} row(s) returned\n")
        return {"query_result": result_str, "error_message": ""}
    except Exception as e:
        error_msg = str(e)
        print(f"[SQL Agent] Execution: ERROR - {error_msg}\n")
        state['db'].rollback()
        return {
            "error_message": f"Execution Error: {error_msg}",
            "validation_status": "INCORRECT",
            "feedback": f"Database returned error: {error_msg}. The query was: {state['sql_query']}. Fix the SQL syntax or column names.",
            "retry_count": state["retry_count"] + 1
        }


def route_input(state: AgentState):
    error = state.get("error_message", "")
    if error == "NOT_MEDICAL":
        return "NOT_MEDICAL"
    if error == "MEDICAL_GENERAL":
        return "MEDICAL"
    return "GENERATE"


def route_validation(state: AgentState):
    if state["validation_status"] == "CORRECT":
        return "EXECUTE"

    if state["retry_count"] > MAX_RETRIES:
        return "MAX_RETRIES"

    return "RETRY"


def route_execution(state: AgentState):
    if state.get("error_message") and "Execution Error" in state["error_message"]:
        if state["retry_count"] > MAX_RETRIES:
            return "END"
        return "RETRY"
    return "END"


builder = StateGraph(AgentState)

builder.add_node("process_input", process_input)
builder.add_node("answer_general", answer_general)
builder.add_node("generate_query", generate_query)
builder.add_node("validate_query", validate_query)
builder.add_node("execute_query", execute_query)

builder.add_edge(START, "process_input")

builder.add_conditional_edges(
    "process_input",
    route_input,
    {
        "GENERATE": "generate_query",
        "MEDICAL": "answer_general",
        "NOT_MEDICAL": END,
    }
)

builder.add_edge("answer_general", END)

builder.add_edge("generate_query", "validate_query")

builder.add_conditional_edges(
    "validate_query",
    route_validation,
    {
        "EXECUTE": "execute_query",
        "RETRY": "generate_query",
        "MAX_RETRIES": END
    }
)

builder.add_conditional_edges(
    "execute_query",
    route_execution,
    {
        "END": END,
        "RETRY": "generate_query"
    }
)


graph = builder.compile()
graph.get_graph().draw_mermaid_png(output_file_path="diagram.png")


def build_history_string(history: list[dict]) -> str:
    if not history:
        return ""
    recent = history[-(MAX_HISTORY_TURNS * 2):]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def run_agent(db: Session, prompt: str, history=None, role: str = None, provider_id: str = None, patient_id: str = None):
    scope_clause = ""
    scope_id = None
    scope_label = ""
    if role and role.upper() == "DOCTOR" and provider_id:
        scope_clause = DOCTOR_SCOPE_CLAUSE.format(provider_id=provider_id)
        scope_id = provider_id
        scope_label = "doctor"
    elif role and role.upper() == "PATIENT" and patient_id:
        scope_clause = PATIENT_SCOPE_CLAUSE.format(patient_id=patient_id)
        scope_id = patient_id
        scope_label = "patient"

    initial_state = {
        "db": db,
        "user_prompt": prompt,
        "original_prompt": prompt,
        "chat_history": build_history_string(history or []),
        "scope_clause": scope_clause,
        "translated_prompt": "",
        "general_answer": "",
        "sql_query": "",
        "query_result": "",
        "error_message": "",
        "validation_status": "",
        "feedback": "",
        "retry_count": 0
    }

    final_state = graph.invoke(initial_state, {"recursion_limit": 20})

    if final_state.get("general_answer"):
        return {"response": final_state["general_answer"]}

    if final_state.get("error_message") == "NOT_MEDICAL":
        return {"response": "I can only help with medical and hospital data questions. Please ask something related to medicine or the hospital database."}

    if scope_clause and scope_id:
        sql = final_state.get("sql_query", "") or ""
        if scope_id not in sql:
            return {
                "response": f"Unable to answer under {scope_label} scope - the generated query did not reference your {scope_label} id. Try rephrasing.",
            }

    if final_state.get("query_result"):
        response = ask_ai(
            PROMPT_RESULT.format(
                initial_prompt=final_state["original_prompt"],
                result=final_state["query_result"]
            )
        )
        return {"response": response, "sql": final_state["sql_query"]}

    if final_state["retry_count"] > MAX_RETRIES:
        return {"response": "I tried multiple times but couldn't build a valid query. Try simplifying your question."}

    return {"response": "Sorry, I couldn't generate a valid result. Please try rephrasing your question."}
