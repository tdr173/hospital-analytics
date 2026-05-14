import re
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .llm_models import ask_ai
from db.db_connector import _db_retrieve
from db.db_data import DB_SCHEMA

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


PROMPT_TRANSLATE = """
You classify and rewrite user messages for a hospital analytics assistant.

User message: "{initial_prompt}"

{chat_context}

Schema reference (for term disambiguation only, do NOT copy into output):
{db_schema}

Classification rules - return EXACTLY one of the three outputs below:

1. DB_RETRIEVAL  - the user is asking for data that exists in the hospital database (patient counts,
   encounter stats, medications, conditions, clusters, sequences, provider info, etc.).
   Output: a single standalone English sentence describing what data to retrieve.
   - Resolve any references to prior turns so the sentence is self-contained with no history needed.
   - Preserve specific entities (names, ids, numbers, date ranges) exactly.

2. MEDICAL_GENERAL - the user is asking a general medical/health question that does NOT require
   querying the database (e.g. "what is diabetes?", "how is hypertension treated?",
   "what are symptoms of COVID-19?", "explain BMI", medical advice questions, etc.).
   Output the literal token followed by a colon and the standalone question in English:
   MEDICAL_GENERAL: <question>

3. NOT_MEDICAL - the input is completely unrelated to medicine or the hospital database
   (greetings, small talk, coding help, math, opinions, commands to modify data, etc.).
   Output the literal token: NOT_MEDICAL

Output ONLY the chosen output. No markdown, no quotes, no extra explanation.
"""

PROMPT_MEDICAL_ANSWER = """
You are a medical assistant for a hospital analytics platform. Answer the following medical question.

{chat_context}

Question: {question}

Rules:
- Reply in the SAME language the user wrote in (English, Romanian, etc.).
- Be accurate and concise: 2-5 sentences or a short bulleted list.
- Do not invent treatments, statistics, or diagnoses that are not medically established.
- If the question implies a personal health situation, add one short sentence advising the user to consult a doctor.
- Never mention SQL, databases, or technical system internals.
"""

PROMPT_GENERATE_SQL = """
You are a PostgreSQL expert writing a SELECT query against a hospital analytics database.

Question: "{prompt}"

Schema:
{db_schema}

{scope_clause}{retry_context}

Output rules:
1. Return ONLY the raw SQL. No markdown, no prose, no trailing semicolon required.
2. ONLY SELECT, or WITH ... SELECT (CTEs). Never INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT/REVOKE/EXEC.
3. Select only the columns needed; never SELECT *.
4. Add LIMIT {max_rows} unless the user asks for "all" results or the query is purely aggregate (COUNT/SUM/AVG/MAX/MIN).
5. Use meaningful aliases for computed columns (e.g. COUNT(*) AS total_patients).
6. ORDER BY so the answer is obvious (e.g. ORDER BY count DESC for "most common", ORDER BY date DESC for "last").

Filtering rules:
7. Descriptive / free-text fields (description, first_name, last_name, city, reason_description, pattern_str) - use ILIKE with %...% wildcards.
8. Categorical codes - use `=` with these exact values:
   - gender: 'M', 'F' (never 'Male'/'Female')
   - marital: 'M', 'S', 'D', 'W'
   - encounter_class: 'inpatient', 'ambulatory', 'outpatient', 'wellness', 'emergency', 'urgentcare', 'home', 'virtual', 'snf', 'hospice'
   - race: 'White', 'Black', 'Asian', 'Native', 'Other'
   - ethnicity: 'Hispanic', 'Non-Hispanic'
9. Alive vs deceased is encoded by deathdate: `deathdate IS NULL` (alive) / `deathdate IS NOT NULL` (deceased).
10. Dates - use EXTRACT(YEAR FROM col) for year, DATE_TRUNC for month/week aggregation, BETWEEN or `>=`/`<` for explicit ranges.
11. Active vs ended for timestamped tables (condition, medication, careplan, allergy) - `end_date IS NULL` means still active.

Distinct-counting rules:
12. Counting or listing patients/providers across clinical tables (condition, medication, procedure, encounter, careplan, etc.) - use COUNT(DISTINCT patient_id) / DISTINCT to avoid duplicates from multiple records per patient.

Clustering rules (cluster_meta, cluster, cluster_patient):
13. cluster_patient is singleton for the current run (no run_id column). Always filter `NOT is_outlier` unless the user explicitly asks about outliers. -1 is the outlier label.
14. cluster_patient.features is JSONB. Access strings with `features->>'key'`; cast numerics with `(features->>'key')::numeric`. Yes/No flags (has_diabetes, has_hypertension, has_heart_disease, has_cancer, is_polypharmacy) are the string 'Yes'/'No'. A missing key returns NULL - do not assume every feature is present.
15. If the user asks about clusters, derive per-cluster metrics from cluster_patient.features - do NOT join clinical tables. If the user asks about raw clinical facts (how many patients have X), use the clinical tables directly.

Sequence-mining rules (prefix_span_pattern, prefix_span_patient_pattern):
16. prefix_span_pattern holds the mined sequences (pattern_str, length, support_count, support_pct). prefix_span_patient_pattern is the (pattern_id, patient_id) junction.
17. To find patients following a pattern → JOIN on pattern_id. To restrict a pattern's membership to a specific cluster → JOIN prefix_span_patient_pattern to cluster_patient on patient_id.
18. Use support_count / support_pct for overall frequency. For cluster-specific frequency use COUNT(DISTINCT pp.patient_id) after joining with cluster_patient.
"""

PROMPT_VALIDATE_SQL = """
You are a SQL QA auditor for a hospital analytics database. Decide if the generated SQL is safe AND correctly answers the user's request.

User Request: "{prompt}"
Generated SQL: {sql_query}

Schema:
{db_schema}

{scope_clause}

Validation checklist (reject if ANY item fails):
1. Must be a single SELECT or WITH ... SELECT. Reject anything that writes data (INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT/REVOKE/EXEC).
2. Every referenced table and column must exist in the schema above.
3. JOIN conditions must use the documented foreign-key relationships.
4. Query logic must answer THIS specific question (right table, right filter, right aggregation). Querying 'patient' when the user asked about 'providers' = NO.
5. For cluster questions: reject if it forgot `NOT is_outlier` (unless the user asked about outliers) or mixed cluster_patient.features with raw clinical tables.
6. For counts of patients/providers across clinical tables: reject if it uses COUNT(*) instead of COUNT(DISTINCT patient_id) when duplicates are likely.
7. If a MANDATORY ROLE SCOPE is present above: reject if the query does not include the required provider_id filter exactly as specified.

Do NOT flag:
- ILIKE vs = (both valid).
- Stylistic preferences: aliasing, ordering, whitespace, column order.
- Presence or absence of LIMIT on aggregate-only queries.

Output format (strict):
Line 1: YES or NO
Line 2 (only if NO): one-sentence explanation of the specific failure.
"""

PROMPT_RESULT = """
Summarise database results for the user in natural language.

User question: "{initial_prompt}"
Database result (list of row dicts): {result}

Rules:
- Reply in the SAME language the user wrote in (English, Romanian, etc.). Match their register.
- Empty result ([] or nothing returned) → say plainly that no matching records were found.
- Single-row single-value result → state it in one sentence with the number and unit where relevant.
- Multi-row result → use a short bulleted or numbered list; truncate to the top ~10 items if longer.
- Never mention SQL, queries, JOINs, tables, columns, or any technical internals. Speak as a data analyst, not a DBA.
- Do not invent or extrapolate values beyond what the result contains.
- Keep it concise: 1-4 sentences or a short list.
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


DOCTOR_SCOPE_CLAUSE = """\

MANDATORY ROLE SCOPE - DOCTOR (provider_id = '{provider_id}'):
- Every SQL query you generate MUST restrict results to encounters where provider_id = '{provider_id}'.
- When the question is about patients, restrict to patients who have at least one encounter with that provider_id. Use: patient.patient_id IN (SELECT DISTINCT patient_id FROM encounter WHERE provider_id = '{provider_id}').
- Never expose other doctors' patients, encounters, or aggregate counts. If the question cannot be answered under this scope, say so in the final answer.
"""


def run_agent(db: Session, prompt: str, history=None, role: str = None, provider_id: str = None):
    scope_clause = ""
    if role and role.upper() == "DOCTOR" and provider_id:
        scope_clause = DOCTOR_SCOPE_CLAUSE.format(provider_id=provider_id)

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

    if scope_clause:
        sql = final_state.get("sql_query", "") or ""
        if provider_id not in sql:
            return {
                "response": "Unable to answer under doctor scope - the generated query did not reference your provider id. Try rephrasing.",
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
