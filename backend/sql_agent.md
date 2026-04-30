# SQL Agent — Architecture & Design

**File:** `app/service/lllm_sql_agent_service/agent_service.py`  
**Model:** OpenAI GPT (configured in `llm_models.py` via `GPT_KEY` env var)  
**Framework:** LangGraph `StateGraph`

---

## Overview

The SQL Agent is a multi-step LangGraph pipeline that translates natural-language questions into PostgreSQL queries, executes them against the hospital database, and returns results as plain-language summaries. It accepts questions about the hospital database (patients, encounters, conditions, medications, clusters, sequences, etc.) as well as general medical knowledge questions. Completely off-topic questions are rejected.

A Mermaid architecture diagram is generated at server startup and written to `diagram.png` in the working directory via:
```python
graph.get_graph().draw_mermaid_png(output_file_path="diagram.png")
```

---

## Graph Nodes

```
START
  └─► process_input
        ├─► [NOT_MEDICAL]  ──────────────────────────────► END
        ├─► [MEDICAL_GENERAL] ──► answer_general ─────────► END
        └─► [DB_RETRIEVAL]  ──► generate_query
                                    └─► validate_query
                                          ├─► [CORRECT]      ──► execute_query
                                          │                          ├─► [OK]    ──► END
                                          │                          └─► [ERROR] ──► generate_query (retry)
                                          ├─► [RETRY]         ──► generate_query
                                          └─► [MAX_RETRIES]  ──────────────────► END
```

---

## Global Constants

| Constant | Value | Purpose |
|---|---|---|
| `MAX_RETRIES` | `3` | Maximum SQL generation + validation retry attempts before giving up |
| `MAX_RESULT_ROWS` | `100` | Default `LIMIT` appended to generated queries |
| `MAX_RESULT_CHARS` | `3000` | Maximum characters of raw DB result passed to the summary prompt |
| `MAX_HISTORY_TURNS` | `5` | Number of Q+A pairs retained from conversation history |

---

## Agent State

Every node reads from and writes to a shared `AgentState` TypedDict that flows through the graph:

| Field | Type | Description |
|---|---|---|
| `db` | `Session` | SQLAlchemy session, passed through untouched |
| `user_prompt` | `str` | Raw user question as received from the API |
| `original_prompt` | `str` | Same as `user_prompt`; preserved so the result summary always uses the clean user question, never a scope-injected variant |
| `chat_history` | `str` | Pre-formatted string of the last `MAX_HISTORY_TURNS` Q+A pairs |
| `scope_clause` | `str` | Role-based restriction text injected into SQL generation and validation (empty for admin, populated for doctor role) |
| `translated_prompt` | `str` | Standalone English retrieval sentence produced by `process_input`; for `MEDICAL_GENERAL` paths this holds the cleaned question |
| `general_answer` | `str` | Set by `answer_general`; non-empty signals a general medical answer was produced without any DB query |
| `sql_query` | `str` | The latest SQL query produced by `generate_query` |
| `query_result` | `str` | Stringified list of row dicts returned by the database, truncated to `MAX_RESULT_CHARS` |
| `error_message` | `str` | Sentinel or execution error message; `"NOT_MEDICAL"` and `"MEDICAL_GENERAL"` are routing sentinels, not real errors |
| `validation_status` | `str` | `"CORRECT"` or `"INCORRECT"` set by `validate_query` |
| `feedback` | `str` | Failure reason passed back to `generate_query` on retry |
| `retry_count` | `int` | Incremented on every failed validation or execution; compared against `MAX_RETRIES` |

---

## Prompts

### 1. `PROMPT_TRANSLATE` — Classification & Rewrite

**Node:** `process_input`  
**Purpose:** Classifies the incoming message into one of three categories and rewrites DB retrieval questions into standalone English sentences.

**Parameters injected:**

| Placeholder | Source | Content |
|---|---|---|
| `{initial_prompt}` | `state['user_prompt']` (+ scope clause prepended when role = DOCTOR) | The user's message, optionally prefixed with the doctor scope clause so the classifier knows the data access context |
| `{chat_context}` | `build_history_string(history)` formatted by `format_chat_context()` | Last 5 Q+A pairs as `User: ... / Assistant: ...` lines, wrapped in a "Conversation history" header; empty string if no history |
| `{db_schema}` | `DB_SCHEMA` from `db/db_data.py` | Full database schema used for term disambiguation only — the model is instructed not to copy it into the output |

**Output — exactly one of:**

| Output | Routing | Meaning |
|---|---|---|
| A standalone English sentence | → `generate_query` | DB data retrieval request |
| `MEDICAL_GENERAL: <question>` | → `answer_general` | General medical/health knowledge question, no DB needed |
| `NOT_MEDICAL` | → `END` | Completely off-topic; rejected |

The classification boundary is:
- **DB_RETRIEVAL**: anything that asks for data present in the hospital database — patient counts, encounter statistics, medication lists, cluster analysis, care trajectories, provider information, etc.
- **MEDICAL_GENERAL**: questions about medical concepts, diseases, symptoms, treatments, or health topics that do not require querying the database (e.g. "what is diabetes?", "how is hypertension treated?").
- **NOT_MEDICAL**: greetings, small talk, coding questions, math, opinions, requests to modify data, or anything unrelated to medicine.

---

### 2. `PROMPT_MEDICAL_ANSWER` — General Medical Q&A

**Node:** `answer_general`  
**Purpose:** Answers general medical knowledge questions directly from the model, without touching the database.

**Parameters injected:**

| Placeholder | Source | Content |
|---|---|---|
| `{question}` | `state['translated_prompt']` | The cleaned standalone question extracted from the `MEDICAL_GENERAL: <question>` output |
| `{chat_context}` | `build_history_string(history)` | Same formatted history string as used in the translate step |

**Constraints applied in the prompt:**
- Reply in the same language the user wrote in.
- 2–5 sentences or a short bulleted list — no long essays.
- Do not invent treatments or diagnoses not medically established.
- If the question implies a personal health situation, add a note advising the user to consult a doctor.
- Never mention SQL, databases, or any system internals.

---

### 3. `PROMPT_GENERATE_SQL` — SQL Generation

**Node:** `generate_query`  
**Purpose:** Produces a raw PostgreSQL `SELECT` query that answers the translated retrieval question.

**Parameters injected:**

| Placeholder | Source | Content |
|---|---|---|
| `{prompt}` | `state['translated_prompt']` | Standalone English retrieval sentence from `process_input` |
| `{db_schema}` | `DB_SCHEMA` | Full schema with table definitions, column types, FK relationships, value enumerations, and example queries |
| `{scope_clause}` | `state['scope_clause']` (+ `"\n\n"` appended) | Doctor scope restriction if role = DOCTOR; empty string otherwise |
| `{retry_context}` | Built from `state['feedback']` and `state['sql_query']` | On first attempt: empty. On retries: a block containing the previous failed SQL and the specific failure reason, instructing the model to fix it |
| `{max_rows}` | `MAX_RESULT_ROWS` (100) | The default LIMIT value to use unless the question asks for all results or uses only aggregate functions |

**Rules enforced in the prompt:**
- Output raw SQL only — no markdown fences, no prose.
- Only `SELECT` or `WITH ... SELECT` (CTEs). All DML/DDL keywords are forbidden.
- Never `SELECT *` — only needed columns.
- `LIMIT {max_rows}` unless the query is purely aggregate or the user asked for all results.
- Meaningful aliases on computed columns; `ORDER BY` to make the answer self-evident.
- `ILIKE '%...%'` for free-text fields; exact enum values for categorical fields (gender `'M'`/`'F'`, encounter_class `'inpatient'`/`'ambulatory'`/etc.).
- `deathdate IS NULL` for alive patients.
- `end_date IS NULL` for active conditions/medications/careplans.
- `COUNT(DISTINCT patient_id)` when counting patients across multi-row clinical tables.
- Cluster queries must filter `NOT is_outlier`; JSONB features accessed with `features->>'key'` / `(features->>'key')::numeric`.
- Sequence queries join `prefix_span_patient_pattern` on `pattern_id`.

---

### 4. `PROMPT_VALIDATE_SQL` — SQL Validation

**Node:** `validate_query`  
**Purpose:** A second LLM call acts as a QA auditor, independently checking that the generated SQL is safe and actually answers the user's question.

**Parameters injected:**

| Placeholder | Source | Content |
|---|---|---|
| `{prompt}` | `state['translated_prompt']` | The retrieval question the SQL must answer |
| `{sql_query}` | `state['sql_query']` | The SQL produced by `generate_query` |
| `{db_schema}` | `DB_SCHEMA` | Full schema for column/table existence checks |
| `{scope_clause}` | `state['scope_clause']` | Doctor scope clause if applicable; empty otherwise |

**Checklist enforced:**
1. Must be a single `SELECT` or `WITH ... SELECT` — no data-modifying statements.
2. Every table and column referenced must exist in the schema.
3. JOINs must use documented foreign-key paths.
4. Query logic must match the question (right table, right filter, right aggregation).
5. Cluster queries must include `NOT is_outlier` unless outliers were explicitly requested.
6. Patient/provider counts must use `COUNT(DISTINCT ...)` where duplicates are possible.
7. If a doctor scope clause is present, the query must include the `provider_id` filter.

**Output:** `YES` (passes) or `NO\n<one-sentence reason>` (fails → retry).  
Stylistic differences (aliasing, whitespace, `ILIKE` vs `=`) are explicitly not flagged.

**Pre-LLM regex check:** Before calling the LLM, `is_select_only()` scans the raw SQL with a regex for `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, `INSERT`, `UPDATE`, `CREATE`, `GRANT`, `REVOKE`, `EXEC`, `EXECUTE`. A match causes an immediate `INCORRECT` without spending a model call.

---

### 5. `PROMPT_RESULT` — Result Summarisation

**Node:** Called inline in `run_agent` after successful execution  
**Purpose:** Converts the raw list of database row dicts into a concise natural-language answer.

**Parameters injected:**

| Placeholder | Source | Content |
|---|---|---|
| `{initial_prompt}` | `state['original_prompt']` | The original user question — always the clean question, never the scope-injected variant — so the summary reads naturally |
| `{result}` | `state['query_result']` | Stringified list of row dicts, truncated to `MAX_RESULT_CHARS` (3000 characters) |

**Rules enforced:**
- Reply in the same language the user wrote in.
- Empty result → say no records were found.
- Single scalar → one sentence with the number and unit.
- Multi-row → bulleted list, top 10 items.
- Never mention SQL, tables, columns, JOINs, or any technical internals.
- Do not extrapolate beyond the returned data.

---

## Medical Scope Enforcement

The agent enforces a strict two-level medical scope:

**Level 1 — Topic classification (PROMPT_TRANSLATE)**  
Every incoming message is classified before any other step. If the model returns `NOT_MEDICAL`, the graph routes directly to `END` and `run_agent` returns the message:
> "I can only help with medical and hospital data questions. Please ask something related to medicine or the hospital database."

No SQL is generated. No DB is touched.

**Level 2 — General medical vs. DB retrieval split**  
Questions classified as `MEDICAL_GENERAL` bypass the entire SQL pipeline and go to `answer_general`, which answers from the model's medical knowledge. This allows questions like "what is diabetes?" or "how is hypertension treated?" to be answered without fabricating database queries.

Together these two levels mean the agent accepts exactly:
- Hospital database queries → SQL pipeline
- General medical knowledge questions → direct LLM answer
- Everything else → rejected

---

## Conversation Memory

Memory is **stateless on the backend** — no database table or server-side session stores history. The frontend is responsible for accumulating the conversation and sending it with every request in the `history` field of `AskAIRequest`.

**API contract (`POST /sql-agent`):**
```json
{
  "question": "How many patients have diabetes?",
  "history": [
    { "role": "user",      "content": "How many patients are there?" },
    { "role": "assistant", "content": "There are 1,234 patients in the database." }
  ]
}
```

**Backend processing:**
1. `build_history_string(history)` takes the last `MAX_HISTORY_TURNS * 2` messages (= 10 messages = 5 Q+A pairs).
2. Each message is formatted as `User: <content>` or `Assistant: <content>`.
3. The resulting string is stored in `state['chat_history']` and injected into both `PROMPT_TRANSLATE` and `PROMPT_MEDICAL_ANSWER` via `format_chat_context()`.

**How history is used:**  
The translate prompt instructs the model to resolve references to prior turns ("what about them?", "same for females?", "and those patients?") using the conversation history, then produce a fully standalone sentence that requires no history to understand. This means `generate_query` and subsequent steps always receive a self-contained question — history is consumed once at the entry point and does not leak into the SQL or validation steps.

---

## Role-Based Scope (Doctor Mode)

When the API caller has the `DOCTOR` role and a `provider_id` is present, a scope clause is built from `DOCTOR_SCOPE_CLAUSE` and stored in `state['scope_clause']`:

```
MANDATORY ROLE SCOPE — DOCTOR (provider_id = '<uuid>'):
- Every SQL query you generate MUST restrict results to encounters where provider_id = '<uuid>'.
- When the question is about patients, restrict to patients who have at least one encounter with that
  provider_id. Use: patient.patient_id IN (SELECT DISTINCT patient_id FROM encounter WHERE provider_id = '<uuid>').
- Never expose other doctors' patients, encounters, or aggregate counts.
```

This clause is injected into:
- `PROMPT_TRANSLATE` — prepended to the user message so the classifier sees the access context.
- `PROMPT_GENERATE_SQL` — included before the output rules so the model hard-wires the filter.
- `PROMPT_VALIDATE_SQL` — included so the auditor rejects any query missing the `provider_id` filter (checklist item 7).

After the graph completes, `run_agent` performs a final regex check: if `provider_id` is not present anywhere in the generated SQL string, the response is replaced with an error message regardless of what the LLM returned.

Doctor scope does **not** apply to `MEDICAL_GENERAL` paths — a doctor asking a general medical knowledge question receives a normal answer without triggering the scope check.

---

## Retry Loop

If `validate_query` returns `INCORRECT`, the state is updated with:
- `validation_status = "INCORRECT"`
- `feedback` = the validator's one-sentence failure reason + the rejected SQL
- `retry_count` incremented by 1

The graph routes back to `generate_query`, which detects non-empty `feedback` and formats a `retry_context` block:
```
IMPORTANT - Your previous query failed. Here is what went wrong:
Previous SQL: <sql>
Error/Feedback: <reason>
Fix the issue and generate a corrected query.
```

If execution itself fails (DB returns an error), the same mechanism fires: `error_message` is set, `feedback` contains the database error + the bad SQL, and `retry_count` is incremented.

The loop continues until either:
- Validation passes and execution succeeds → result summary returned.
- `retry_count > MAX_RETRIES` (3) → graph exits and returns a "couldn't build a valid query" message.

Maximum total LLM calls for a single question: `1 (translate) + (MAX_RETRIES + 1) * 2 (generate + validate) + 1 (result) = 10`.
