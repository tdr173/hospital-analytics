import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

from .llm_models import ask_ai
from db.db_connector import _db_retrieve
from db.db_data import DB_SCHEMA

load_dotenv()

MAX_RETRIES = 3
MAX_RESULT_ROWS = 100
MAX_RESULT_CHARS = 3000

DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE
)


class AgentState(TypedDict):
    user_prompt: str
    chat_history: str
    translated_prompt: str
    sql_query: str
    query_result: str
    error_message: str
    validation_status: str
    feedback: str
    retry_count: int


PROMPT_TRANSLATE = """
You are a technical translator for a hospital analytics system.
User Prompt: "{initial_prompt}"
Database Schema: {db_schema}

{chat_context}

Task:
1. Use the conversation history (if any) to resolve references like "what about", "same but for", "and those", "how many of them", etc. The refined prompt must be a STANDALONE question that makes sense without the history.
2. Translate the prompt to English if necessary.
3. Refine it to be a precise technical request for a database retrieval.
4. If the prompt is NOT a data retrieval request (e.g. greetings, opinions, commands to modify data), return exactly "NOT_RETRIEVAL".

Output: ONLY the refined prompt string or "NOT_RETRIEVAL". No explanations.
"""

PROMPT_GENERATE_SQL = """
You are a PostgreSQL expert for a hospital analytics database.
Goal: Write a SELECT query for: "{prompt}"

Schema:
{db_schema}

{retry_context}

Rules:
1. Return ONLY the raw SQL query. No markdown, no explanations.
2. ONLY use SELECT (or WITH ... SELECT for CTEs). Never use INSERT, UPDATE, DELETE, DROP, ALTER, or any data-modifying statement.
3. Select ONLY the columns needed to answer the question - never use SELECT *.
4. Always add LIMIT {max_rows} unless the user explicitly asks for all results or the query uses aggregation (COUNT, SUM, AVG, etc.).
5. Use ILIKE for searching descriptive/name fields (description, first_name, last_name, city, reason_description).
6. Use = for categorical fields with fixed values: gender ('M'/'F'), encounter_class ('inpatient','ambulatory','wellness','emergency','urgentcare'), marital ('M','S','D','W'), race, ethnicity.
7. Handle dates correctly: use EXTRACT(YEAR FROM date_column) for year filtering.
8. Use meaningful column aliases for computed fields (e.g. COUNT(*) AS total_patients).
9. Order results in a way that makes the answer clear (e.g. ORDER BY count DESC for "most common").
10. When counting or listing patients/providers across clinical tables (condition, medication, etc.), use COUNT(DISTINCT patient_id) or SELECT DISTINCT to avoid duplicates from multiple records.
11. For cluster_patient.features JSONB access: strings use features->>'key'; numerics must be cast e.g. (features->>'age')::numeric. Yes/No flags (has_diabetes, has_hypertension, has_heart_disease, has_cancer, is_polypharmacy) are string 'Yes'/'No'. There is no run_id column — cluster_patient holds only the current run. Filter NOT is_outlier unless outliers were explicitly requested.
12. Never mix clinical tables (condition, medication, encounter, etc.) with cluster_patient.features for the same metric: if the user asks about clusters, derive counts from features; otherwise use the clinical tables directly.
"""

PROMPT_VALIDATE_SQL = """
You are a SQL QA auditor for a hospital analytics database.
User Request: "{prompt}"
Generated SQL: "{sql_query}"
Schema: {db_schema}

Task: Verify if the SQL is correct and safe for the given request.

Validation checklist:
1. The query must be a SELECT statement only (CTEs with WITH...SELECT are allowed). Any INSERT/UPDATE/DELETE/DROP = instant NO.
2. All referenced tables and columns must exist in the schema.
3. The query logic must match what the user asked (e.g. don't query 'patient' when user asks about 'providers').
4. JOINs must use correct foreign key relationships as defined in the schema.
5. Do NOT flag ILIKE vs = as an error. Both are valid.
6. Do NOT flag stylistic preferences (aliasing, ordering, formatting).

Output Format:
Line 1: YES or NO
Line 2: (If NO) Brief explanation of the specific error found.
"""

PROMPT_RESULT = """
The user asked: "{initial_prompt}"
The database returned: {result}

Task:
- Generate a clear, helpful response in the same language as the user's question.
- If the result is empty or [], say that no matching records were found.
- Present numbers and data clearly. Use bullet points or short lists for multiple items.
- Keep the response concise - no more than 3-4 sentences for simple questions, or a short formatted list for multi-row results.
- Do not mention SQL, queries, or technical database details.
"""


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
    prompt = PROMPT_TRANSLATE.format(
        initial_prompt=state['user_prompt'],
        db_schema=DB_SCHEMA,
        chat_context=format_chat_context(state.get('chat_history', ''))
    )
    result = ask_ai(prompt).strip()

    if "NOT_RETRIEVAL" in result:
        return {"error_message": "NOT_RETRIEVAL"}

    return {
        "translated_prompt": result,
        "retry_count": 0,
        "feedback": ""
    }


def generate_query(state: AgentState):
    retry_context = ""
    if state.get('feedback'):
        retry_context = (
            f"IMPORTANT - Your previous query failed. Here is what went wrong:\n"
            f"Previous SQL: {state.get('sql_query', 'N/A')}\n"
            f"Error/Feedback: {state['feedback']}\n"
            f"Fix the issue and generate a corrected query."
        )

    prompt = PROMPT_GENERATE_SQL.format(
        prompt=state['translated_prompt'],
        db_schema=DB_SCHEMA,
        retry_context=retry_context,
        max_rows=MAX_RESULT_ROWS,
    )

    raw_response = ask_ai(prompt)
    clean_sql = extract_clean_sql(raw_response)

    return {"sql_query": clean_sql}


def validate_query(state: AgentState):
    sql = state['sql_query']

    if not is_select_only(sql):
        return {
            "validation_status": "INCORRECT",
            "feedback": f"Query contains forbidden statements. Only SELECT queries are allowed. Generated SQL was: {sql}",
            "retry_count": state["retry_count"] + 1
        }

    prompt = PROMPT_VALIDATE_SQL.format(
        prompt=state['translated_prompt'],
        sql_query=sql,
        db_schema=DB_SCHEMA
    )

    response = ask_ai(prompt)

    if response.strip().upper().startswith("YES"):
        return {"validation_status": "CORRECT", "feedback": ""}
    else:
        lines = response.split('\n')
        feedback = lines[1] if len(lines) > 1 else response
        return {
            "validation_status": "INCORRECT",
            "feedback": f"Validation rejected the SQL: {feedback}. The query was: {sql}",
            "retry_count": state["retry_count"] + 1
        }


def execute_query(state: AgentState):
    try:
        result = _db_retrieve(state['sql_query'])
        result_str = truncate_result(str(result))
        return {"query_result": result_str, "error_message": ""}
    except Exception as e:
        error_msg = str(e)
        return {
            "error_message": f"Execution Error: {error_msg}",
            "validation_status": "INCORRECT",
            "feedback": f"Database returned error: {error_msg}. The query was: {state['sql_query']}. Fix the SQL syntax or column names.",
            "retry_count": state["retry_count"] + 1
        }


def route_input(state: AgentState):
    if state.get("error_message") == "NOT_RETRIEVAL":
        return "END"
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
builder.add_node("generate_query", generate_query)
builder.add_node("validate_query", validate_query)
builder.add_node("execute_query", execute_query)

builder.add_edge(START, "process_input")

builder.add_conditional_edges(
    "process_input",
    route_input,
    {
        "GENERATE": "generate_query",
        "END": END
    }
)

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


MAX_HISTORY_TURNS = 3


def build_history_string(history: list[dict]) -> str:
    if not history:
        return ""
    recent = history[-(MAX_HISTORY_TURNS * 2):]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def run_agent(prompt, history=None):
    initial_state = {
        "user_prompt": prompt,
        "chat_history": build_history_string(history or []),
        "translated_prompt": "",
        "sql_query": "",
        "query_result": "",
        "error_message": "",
        "validation_status": "",
        "feedback": "",
        "retry_count": 0
    }

    final_state = graph.invoke(initial_state, {"recursion_limit": 20})

    if final_state.get("error_message") == "NOT_RETRIEVAL":
        return {"response": "I can only help with data retrieval questions. Please ask something about the database."}

    if final_state.get("query_result"):
        response = ask_ai(
            PROMPT_RESULT.format(
                initial_prompt=final_state["user_prompt"],
                result=final_state["query_result"]
            )
        )
        return {"response": response, "sql": final_state["sql_query"]}

    graph.get_graph().draw_mermaid_png(output_file_path="diagram.png")

    if final_state["retry_count"] > MAX_RETRIES:
        return {"response": "I tried multiple times but couldn't build a valid query. Try simplifying your question."}

    return {"response": "Sorry, I couldn't generate a valid result. Please try rephrasing your question."}


