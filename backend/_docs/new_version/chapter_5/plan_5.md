# Chapter 5 — Detailed Design and Implementation — Revision Plan

This plan describes how the **final** `design_implementation.tex` should look after the
architecture changes. It lists what to remove, what to reframe, and what new material to add
so the chapter matches the code (a **monolith**, no Docker/microservices, demo-only roles).

## Progress (updated)

**Done in the tex** (delete / reframe pass):
- §1 — all Docker / microservice / RabbitMQ / Traefik / mail-service references removed. ✅
- §3 — §5.2 intro rewritten to the monolith; `General Architecture` stubs replaced by
  **Layered Backend** + **Frontend Architecture**; module "microservice" attributions removed. ✅
- Prompts refreshed to match `app/prompts/*` and tied to Liu et al. `\cite{liu2025}`
  (evidence-based framing, bias mitigation, chain-of-thought, decision-support-not-diagnosis,
  medical-answer disclaimer); `DOCTOR_SCOPE_CLAUSE` reframed as a role-separation demo. ✅

**Now written in the tex** (this implementation pass):
- §4 → `5.1.6 Analytics Pipeline Orchestration Design` (+ Figure 5). ✅
- §8 → `5.1.7 Database Design` (+ Figure 6, the ER diagram). ✅
- `5.2.2 Backend Implementation` (+ Figure 7) and `5.2.3 Frontend Implementation`. ✅
- §5 → `5.2.8 Pipeline Orchestration Implementation` (+ Figure 8, orchestrator/guard/scheduler
  listings). ✅
- §7 → `Class Design of the Core Components` subsection (+ Figure 9). ✅
- §6 → `5.3 Running and Operations` section. ✅

**Still pending** (cannot be done from text — needs you):
- The 5 new figures are inserted as **placeholders** (`figs/chapter_5/figure5.png` … `figure9.png`);
  upload the real images. Contents specified in the "Figure specifications" section at the end.
- Diagram regeneration of the two *existing* figures: `system_architecture.png` /
  `system_design.png` still show container/microservice boxes and should be redrawn as a
  layered-monolith package diagram.
- Intentionally **not** added (would duplicate existing material): a separate `5.1.1 System
  Architecture` (the 5.1 intro + `system_design.png` already serve this) and `5.1.5 SQL Agent
  Design` (covered by the directed-graph formalization in Chapter 4). Say if you want them anyway.

The numbered sections below keep the full spec; §1 and §3 record what was already changed.

---

## 0. Ground truth (the architecture the chapter must describe)

- **Monolithic application.** One Next.js frontend, one FastAPI backend process, one
  PostgreSQL database. No Docker, no containers, no microservices, no Traefik/reverse proxy,
  no RabbitMQ / message broker, no separate mail / auth / users / analytics / clinical-core
  / queue services. Everything the old draft split into services is a **package/module inside
  the single backend**.
- **Backend is strictly layered** (from `CLAUDE.md`): `api/ (routers) → service/ →
  repository/ → domain/ (models + schemas)`. Routers are aggregated in `app/api/__init__.py`
  and registered in `app/main.py`.
- **No real authentication.** The three roles (MANAGER, DOCTOR, PATIENT) exist **only to
  demonstrate how the UI and data scope change per role** for the research/demo. There is no
  login security, no token/session hardening, no auth service. `rolePermissions.ts` gates
  routes on the frontend; the backend `DOCTOR_SCOPE_CLAUSE` shows role-scoped querying. Both
  are **demonstrations of role-aware behaviour, not a security boundary** — say this explicitly.
- **New: an in-process analytics pipeline orchestration job.** A single job chains
  `ETL (only if the DB is empty) → K-Prototypes clustering → global sequence mining →
  per-cluster sequence mining`. It can be **triggered manually from the GUI by the manager**
  and also runs on an **in-process monthly schedule** (APScheduler). It replaces the old
  "run each script by hand, offline" story: the heavy scripts are still standalone-runnable,
  but now also expose entry points the orchestrator calls from a background daemon thread.

---

## 1. Global edits — remove / reframe across the whole chapter — ✅ DONE

Done in the tex. Retained as a record of what changed (except diagram regeneration, still pending):

| Current text (approx. line) | Action |
|---|---|
| 5.1 intro: "...backend, and **containerization**" (l.5) | Drop "containerization"; replace with "and the analytics pipeline orchestration". |
| System Design intro: "...containerized with Docker" (plan/diagram) | Remove Docker; the `system_design.png` diagram must be regenerated with no container boxes. |
| 5.2 intro: "works as **Dockerized microservices**... AI Service... **mail service**... **RabbitMQ**" (l.153) | Rewrite entirely (see §3). Monolithic FastAPI + Next.js + PostgreSQL; algorithmic modules are libraries called in-process. |
| "This script is part of the **analytics microservice**" (ETL, l.181) | Delete the microservice attribution; call it a module in the backend, runnable standalone or via the pipeline. |
| "part of the **ml-batch microservice**" (K-Prototypes, l.332) | Same — remove; it is `app/clustering_algorithms/k_prototypes/`. |
| "part of the **ml-batch service**" (PrefixSpan, l.725) | Same — remove; it is `app/clustering_algorithms/prefix_span/`. |
| "inside the **analytics microservice**" (SQL agent, l.860) | Same — remove; it is `app/service/lllm_sql_agent_service/`. |
| Any figure/table referencing Docker Compose, service mesh, brokers | Remove or regenerate. |

Keep (these are real and correct): the ETL logic, K-Prototypes pipeline, PrefixSpan pipeline,
and the LangGraph SQL agent internals (prompts, validator, retry loop, `DOCTOR_SCOPE_CLAUSE`).
Only their **packaging/deployment framing** is wrong.

---

## 2. Target section structure

```
5.1 Detailed Design
    5.1.1 System Architecture (monolith overview + why FastAPI / PostgreSQL / Next.js)
    5.1.2 Synthea Data Ingestion and ETL Pipeline        [keep]
    5.1.3 K-Prototypes Clustering Design                 [keep]
    5.1.4 Pattern Mining Design                          [keep]
    5.1.5 SQL Agent Design                               [light: LangGraph as in-process module]
    5.1.6 Analytics Pipeline Orchestration Design        [NEW]
    5.1.7 Database Design (ER diagram, incl. pipeline_run singleton)
5.2 Detailed Implementation
    5.2.1 General Architecture (layered monolith: api → service → repository → domain)
    5.2.2 Backend Implementation (routing→service→repository, Pydantic/CamelModel, env-var DB config)
    5.2.3 Frontend Implementation (Next.js App Router, Redux slices/thunks, role-gated routes)
    5.2.4 ETL Pipeline Implementation                    [keep]
    5.2.5 K-Prototypes Pipeline Implementation           [keep]
    5.2.6 PrefixSpan Pipeline Implementation             [keep]
    5.2.7 LLM SQL Agent Implementation                   [keep]
    5.2.8 Pipeline Orchestration Implementation          [NEW]
5.3 Running and Operations                               [replaces "5.4 Deployment"]
```

The three analytics modules keep their existing (strong) design + implementation text; the
only change there is deleting the microservice sentences.

---

## 3. Rewrite 5.2 intro + 5.2.1 General Architecture (the biggest change) — ✅ DONE (text); diagram still pending

The prose is written. What was done (and the `system_architecture.png` regeneration that is *not*):
Replaced the "Dockerized microservices / Traefik / Auth-Users-Analytics-Clinical-Core-Queue-
Mail / RabbitMQ" material with a **monolithic layered architecture**:

- **One-paragraph system overview**: Next.js (frontend, REST client) ↔ FastAPI (single backend
  process) ↔ PostgreSQL. The analytics capabilities (K-Prototypes clustering, PrefixSpan mining,
  LangGraph SQL agent) are **modules imported and called inside the backend**, not network
  services. Justify the monolith: single developer, single deployment target, shared DB engine
  and models, no need for independent scaling or inter-service messaging — a monolith removes the
  operational overhead (brokers, service discovery, network hops) that a microservice split would
  add without benefit at this scale.
- **Layered backend** (this is the diagram to draw — a package diagram, not a deployment diagram):
  `api/` routers → `service/` (business logic, delegates) → `repository/` (all SQL) → `domain/`
  (SQLModel models + Pydantic/CamelModel schemas). State the rule: no cross-layer imports; static
  routes registered before dynamic ones; routers aggregated in `app/api/__init__.py`.
- **In-process background work**: an APScheduler `BackgroundScheduler` and daemon threads run
  inside the same process (cluster-detail cache warm-up on startup, and the monthly pipeline job).
  No external worker/queue.
- **Roles without auth**: one short paragraph — roles are a **demonstration layer**. Frontend
  `rolePermissions.ts` maps route prefixes to allowed roles (e.g. `/pipeline`, `/clusters`,
  `/statistics` → MANAGER only); the SQL agent's `DOCTOR_SCOPE_CLAUSE` shows how a doctor's
  queries would be scoped to their `provider_id`. Explicitly note this is to illustrate per-role
  UX/data-scope, **not** a hardened access-control system.
- Delete the `Traefik`, `Auth Service`, `Users Service`, `Analytics Service`, `Clinical Core
  Service`, `Queue Service`, `Mail Service` subsubsections entirely.

Regenerate `system_architecture.png` as a layered/package diagram of the single backend.

---

## 4. NEW — 5.1.6 Analytics Pipeline Orchestration Design — ✅ DONE (Figure 5 placeholder)

Describe the pipeline as a **state machine over a singleton `pipeline_run` row**:

- **Purpose**: turn the three previously-manual scripts into one coherent, observable job that a
  manager can trigger from the UI and that also runs on a schedule.
- **Stages** (sequential): `ETL` (only if the `patient` table is empty — otherwise skipped) →
  `CLUSTERING` → `SEQUENCES_GLOBAL` → `SEQUENCES_CLUSTERS` (labels `0..k-1` plus `-1` outliers) →
  `DONE`. Status is one of `IDLE | RUNNING | SUCCESS | FAILED`.
- **Two triggers, one orchestrator**: (a) manual — manager clicks *Start* → `POST /pipeline/run`;
  (b) scheduled — APScheduler cron (1st of month, 02:00). Both call the same `run_pipeline()`.
- **Concurrency safety**: an atomic guard flips the singleton to `RUNNING` only if it is not
  already running (guards double-clicks and manual/scheduled overlap).
- Suggested figure: a **black-box + state diagram** — input (trigger source), the linear stage
  progression writing status into `pipeline_run`, output (populated `cluster*` and
  `prefix_span_pattern` tables). Mention this ties the ETL/clustering/mining modules (each
  described on its own later) into a single flow.

---

## 5. NEW — 5.2.8 Pipeline Orchestration Implementation — ✅ DONE (Figure 8 placeholder)

Concrete implementation, with 1–2 short listings:

- **State table**: `PipelineRunModel` (SQLModel, `pipeline_run`, singleton `id=1`) — fields
  `status`, `current_stage`, `etl_skipped`, `triggered_by` (`manual`/`scheduled`),
  `started_at`, `finished_at`, `last_run_at`, `error`.
- **Orchestrator** (`service/pipeline_service/orchestrator.py`, `run_pipeline(triggered_by)`):
  never raises — records failure on the row; opens a short-lived `SessionLocal()` per stage;
  calls `run_etl(engine)` (conditionally), `run_clustering_stage(engine)`,
  `prefix_span.run(engine, db, n_clusters=None)`, then loops `prefix_span._run_single(...)` over
  cluster labels. This is the sentence that supersedes the old "these scripts are run offline by
  hand" framing: the scripts still run standalone, **and** expose these callable entry points.
- **Service** (`PipelineService`): `start_manual()` spawns `run_pipeline` in a **daemon
  `threading.Thread`** so the HTTP request returns immediately and the FastAPI event loop is not
  blocked; refuses if already `RUNNING`. `get_status()` (lightweight poll) and `get_overview()`
  (adds data counts, interpreted-clusters/sequences progress, `last_run`/`next_run`).
- **Scheduler wiring** (`app/main.py` lifespan): `BackgroundScheduler` +
  `CronTrigger(day=1, hour=2, minute=0)`, `id="monthly_pipeline"`, stored on `app.state.scheduler`
  so endpoints can read `next_run_time`; shut down on app exit. Note the `pipeline_run` singleton
  is seeded at startup.
- **Endpoints** (`api/pipeline/`): `POST /pipeline/run` (409 if already running),
  `GET /pipeline/status`, `GET /pipeline/overview`.
- **Frontend** (`app/(main)/pipeline/`, MANAGER-only via `rolePermissions.ts`): Redux
  slice+thunks; the page fetches the overview once, then **polls `status` every 2 s while
  RUNNING**, and refetches the full overview when the run finishes — this is the live
  stage/progress UI the manager sees. Reference `PipelineRunCard` and `PipelineStatsGrid`.

---

## 6. Replace "5.4 Deployment" with "5.3 Running and Operations" — ✅ DONE

No Docker Compose / container / network / ports / deployment diagram. Instead:

- Single-process run: `uvicorn app.main:app` (backend, :8000), `npm run dev`/`build` (frontend).
- Configuration via `.env` + `python-dotenv` (POSTGRES_*, GEMINI_API_KEY, GPT_KEY) — same
  codebase points at different DB instances with no code change.
- Startup work done in the FastAPI lifespan: `create_all`, idempotent `ALTER/INDEX` migrations,
  observation materialized views, cluster-detail cache warm-up thread, pipeline singleton seed,
  and the monthly scheduler.
- The heavy analytics scripts can be run standalone from the CLI **or** via the orchestrated job.

---

## 7. Class-diagram requirement (still required by the brief) — ✅ DONE (Figure 9 placeholder)

Keep the note that the chapter needs real UML class diagrams (attributes + methods) for the
2–3 most important classes per major component. Candidates, now including the pipeline:

- `PipelineService` (`start_manual`, `get_status`, `get_overview`) + `PipelineRepository`
  (`try_mark_running`, `set_stage`, `mark_success`, `mark_failed`) + `PipelineRunModel` — plus the
  orchestrator's stage flow.
- Clustering: the K-Prototypes wrapper (feature build → scale → fit → evaluate → persist → AI).
- Sequence mining: the PrefixSpan miner (`run`, `_run_single`, scoring, dedup).
- SQL agent: the LangGraph node functions over the shared typed state.

---

## 8. NEW — 5.1.7 Database Design — ✅ DONE (Figure 6 placeholder)

New section with an ER diagram plus explanatory text. The 18 tables split cleanly into two
groups; frame the section around that split.

### Group A — Normalized raw-data relations (the ingested Synthea CSVs) — 11 tables (+1 junction)

These mirror the Synthea CSVs one-to-one and hold the raw EHR data (already covered by the ETL
section §5.2.4). Describe the normalization: every table has its own primary key, non-key
attributes fully depend on it, and many-to-many links go through junction tables.

- **Core / infrastructure entities (4):** `patient`, `organization`, `provider`, `encounter`.
  `encounter` is the hub: FK → `patient` and FK → `provider`; `provider` FK → `organization`.
- **Clinical event tables (7):** `condition`, `medication`, `procedure`, `observation`,
  `immunization`, `allergy`, `careplan`. Each carries FK → `patient` (and, where relevant,
  → `encounter`). `observation` is the largest (millions of rows), which is why it is
  pre-aggregated by materialized views for the statistics dashboard.
- **Junction (1):** `patient_provider` — the many-to-many bridge between `patient` and
  `provider`, materialized during ETL from `encounter` via `SELECT DISTINCT` (unique constraint
  on `(patient_id, provider_id)`).

### Group B — Application / analytics tables (produced and consumed by the pipeline + API) — 6 tables

These are not part of the raw dataset; they store the outputs of the analytics pipeline and
the pipeline's own state. Note the two JSONB conventions (`features`, `ai_analysis`, `metrics`,
`params`, `detail_cache`) and the two singleton tables.

- **`cluster_meta`** (singleton, one row): metadata of the current K-Prototypes run —
  `algorithm`, `n_clusters`, `n_patients`, `n_outliers`, `numerical_features` /
  `categorical_features` (JSONB), `params` (JSONB), `metrics` (JSONB), `heatmap` / `pca_image`
  (BYTEA), `ai_analysis` (JSONB). A re-run DELETEs then INSERTs this row.
- **`cluster`**: one row per cluster label (`0..k-1` and `-1` for outliers) — `cluster_label`,
  `color`, `title`, `description`, `insight`, `recommendation`, `ai_analysis` (JSONB, lazy),
  `detail_cache` (JSONB). Holds the LLM-generated card content.
- **`cluster_patient`**: assignment of each patient to a cluster — `patient_id` (FK →
  `patient`), `cluster_label`, `is_outlier`, `pca_x` / `pca_y`, and `features` (JSONB cache of
  all numerical + categorical per-patient features for fast retrieval).
- **`prefix_span_pattern`**: the mined closed sequential patterns — `rank`, `pattern_str`,
  `length`, `support_count`, `support_pct`, `cluster_label` (nullable: `NULL` = global scope,
  otherwise the per-cluster scope), `ai_analysis` (JSONB, lazy).
- **`prefix_span_patient_pattern`**: junction (`pattern_id` FK → `prefix_span_pattern`,
  `patient_id`) recording which patients follow each pattern; enables patient→sequences,
  sequence→patients, and cluster→sequences (join to `cluster_patient` on `patient_id`).
- **`pipeline_run`** (singleton, one row): the orchestration state machine (see §5.2.8) —
  `status`, `current_stage`, `etl_skipped`, `triggered_by`, `started_at` / `finished_at` /
  `last_run_at`, `error`.

### Diagram + text notes

- Draw the ER diagram with the two groups visually separated (raw CSV block vs. analytics block).
  The only hard FK from Group B into Group A is `cluster_patient.patient_id → patient`; the other
  analytics links (`prefix_span_patient_pattern.patient_id`, `cluster_label` fields) are logical
  joins, not enforced FKs — say so explicitly.
- Mention the singletons (`cluster_meta`, `pipeline_run`) and the "one row per label" nature of
  `cluster`, since they are unusual and worth a sentence.
- Keep the count honest: **11 normalized CSV relations + 1 ETL junction + 6 analytics/pipeline
  tables = 18** (the SQL agent's `DB_SCHEMA` exposes only a curated subset of these to the LLM).

---

## 9. Writing reminders (unchanged)

- Every diagram gets explanatory text; every listing 10–20 lines, illustrative only.
- Justify decisions (why monolith, why in-process scheduler over a broker, why MinMax scaler…).
- Keep cluster/label terminology identical to the results chapter.
- General → specific, design → implementation.

---

## 10. Figure specifications (new placeholders to produce)

Five new figures were inserted into the tex as placeholders at `figs/chapter_5/figureN.png`.
The pre-existing figures (already made) are untouched. What each new one must contain:

- **Figure 5 — `figure5.png` — Pipeline orchestration: stages and state transitions** (§5.1.6).
  A state / flow diagram. Show the four statuses (`IDLE → RUNNING → SUCCESS`, and `RUNNING →
  FAILED`) and, inside `RUNNING`, the linear stage chain
  `ETL (skipped if DB not empty) → CLUSTERING → SEQUENCES_GLOBAL → SEQUENCES_CLUSTERS → DONE`.
  Indicate the two triggers feeding the same job (manual = manager button, scheduled = monthly
  cron) and the atomic "already running?" guard that rejects a second trigger.

- **Figure 6 — `figure6.png` — Entity–Relationship diagram** (§5.1.7).
  The 18 tables in two visually separated blocks. Block A (raw Synthea CSVs): `patient`,
  `organization`, `provider`, `encounter` (hub) + the 7 clinical tables + `patient_provider`
  junction, with the real FKs. Block B (analytics): `cluster_meta`, `cluster`, `cluster_patient`,
  `prefix_span_pattern`, `prefix_span_patient_pattern`, `pipeline_run`. Draw the one hard FK
  B→A (`cluster_patient.patient_id → patient`) solid and the logical joins dashed. Mark the
  singletons (`cluster_meta`, `pipeline_run`) and JSONB columns.

- **Figure 7 — `figure7.png` — Request lifecycle across the backend layers** (§5.2.2).
  A layered / sequence diagram of one request: Client → Router (`api/`) → Service (`service/`)
  → Repository (`repository/`) → PostgreSQL, and the domain models (`domain/`) flowing back up.
  Show validation (Pydantic/CamelModel) at the router boundary and the `get_db()` session scope.

- **Figure 8 — `figure8.png` — Pipeline management page (manager view)** (§5.2.8).
  A screenshot of the `/pipeline` page: the run card (status, current stage, Start button) and
  the statistics grid (data counts, interpreted clusters/sequences, last/next run). Ideally
  captured mid-run so the live stage indicator is visible.

- **Figure 9 — `figure9.png` — Class diagram of the core components** (§ Class Design).
  UML classes with attributes + methods. At minimum: `PipelineService`
  (`start_manual`, `get_status`, `get_overview`) → `PipelineRepository` (`try_mark_running`,
  `set_stage`, `mark_success`, `mark_failed`) → `PipelineRunModel`; plus the clustering wrapper
  around `KPrototypes` and the mining module around `PrefixSpan` (`run`, `_run_single`). Show the
  service→repository→model dependency direction.

Also still to redo (existing figures, not placeholders): `system_design.png` and
`system_architecture.png` must be redrawn without Docker/microservice/broker boxes, as a
layered-monolith package diagram.

---

## 11. Chapter 5 sections — pre-existing vs. added

Snapshot of the chapter after this pass. "Existing" = was already in the tex (kept, some
lightly edited to drop Docker/microservice framing); "Rewritten" = existing heading, body
replaced; "Added" = new in this work.

**5.1 Detailed Design**
- Intro + `system_design.png` figure — *existing* (intro reworded, no "containerization").
- Synthea Data Ingestion and ETL Pipeline — *existing*.
- K-Prototypes Clustering Design — *existing*.
- Pattern Mining Design — *existing*.
- Analytics Pipeline Orchestration Design — **added** (§5.1.6, Figure 5).
- Database Design — **added** (§5.1.7, Figure 6).

**5.2 Detailed Implementation**
- Intro paragraph — *rewritten* (monolith instead of Dockerized microservices).
- General Architecture — *rewritten* (Traefik/Auth/Users/Analytics/Clinical-Core/Queue/Mail
  stubs replaced by `Layered Backend` + `Frontend Architecture`).
- Backend Implementation — **added** (§5.2.2, Figure 7).
- Frontend Implementation — **added** (§5.2.3).
- ETL Pipeline Implementation — *existing* (microservice line removed).
- K-Prototypes Pipeline Implementation — *existing* (microservice line removed; prompts updated).
- PrefixSpan Pipeline Implementation — *existing* (microservice line removed).
- LLM SQL Agent Implementation — *existing* (microservice line removed; prompts updated + Liu et al.).
- Pipeline Orchestration Implementation — **added** (§5.2.8, Figure 9).
- Class Design of the Core Components — **added** (Figure 8).

**5.3 Running and Operations** — **added** (replaces the never-written Docker "Deployment").

Not added on purpose (would duplicate existing material): `5.1.1 System Architecture` and
`5.1.5 SQL Agent Design`.
