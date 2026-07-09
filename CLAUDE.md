# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hospital analytics platform with a **Next.js 16 frontend** and **FastAPI backend**, connected to a PostgreSQL database. Features patient management, clustering analysis (k-prototypes ML), statistics dashboards, and an LLM-powered SQL agent.

---

## Writing

- Editing for AI patterns → read `SKILL.md`

---

## Commands

### Frontend (`/frontend`)
```bash
npm run dev      # dev server on :3000 (Turbopack)
npm run build    # production build
npm run lint     # ESLint
```

### Backend (`/backend`)
```bash
# From /backend directory
uvicorn app.main:app --reload   # dev server on :8000
```
Backend requires a `.env` file at `backend/` with: `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `GEMINI_API_KEY`, `GPT_KEY`.

---

## Architecture

### Frontend

**Routing**: Next.js App Router with two route groups:
- `app/(auth)/` — login, forgot-password
- `app/(main)/` — nested layouts for `/patients`, `/clusters`, `/statistics`, `/home`

**State management**: Redux Toolkit. All server data lives in slices under `store/slices/`. Each domain has a `thunks.ts` (async API calls) and a `*-slice.ts` (state shape + reducers).

**API calls**: All thunks use a local `get<T>(url, label)` helper that fetches with `ngrok-skip-browser-warning: true` header and shows a `toast.error()` (with unique `toastId` to prevent StrictMode duplicates) on failure. `API_BASE` (`http://localhost:8000`) is defined in `store/slices/clusters/thunks.ts` and re-exported from there.

**Styling**: Emotion CSS via the custom `useClasses(stylesObject, { name })` hook in `utils/useClasses.ts`. Styles live in co-located files:
- Pages/layouts → `styles.ts` in the same directory
- Components → `ComponentNameStyles.ts` in the component folder

Rules:
- Never move `sx={{}}` (MUI prop) to style files
- Dynamic/API-driven values (e.g. cluster colors from backend) stay as inline `style={{}}`
- All other hardcoded styles go into `styles.ts` / `ComponentNameStyles.ts`
- To see class keys in DevTools, set `NEXT_PUBLIC_SHOW_CLASSNAMES=true` in `.env.local`

**Theme**: `utils/theme.ts` — single source of truth for colors, spacing, typography, borderRadius, shadows. Always reference theme values rather than hardcoding.

**MUI components**: Used for table, form inputs, tabs. Custom styled wrappers live in `components/generic_components/` (StyledTable, StyledButton, StyledDropdown, StyledInput, StyledDatePicker, etc.).

**Charts**: ECharts (via `echarts-for-react`) and Recharts. Chart wrapper components are in `components/generic_components/`.

### Backend

**Layer structure** (strict top-down, no cross-layer imports):
```
api/ (routers) → service/ → repository/ → domain/models + domain/schemas
```

Each domain (`patients`, `clusters`, `statistics`) has:
- `api/<domain>/` — one file per endpoint, imported via `__init__.py` with wildcard re-exports
- `service/<domain>_service/` — thin delegation to repository
- `repository/<domain>_repository/` — all DB queries (SQLAlchemy `text()` for complex SQL)
- `domain/schemas/<domain>_schemas/` — Pydantic/SQLModel request+response models

**Router registration**: `app/api/__init__.py` aggregates routers; `app/main.py` registers them. Order matters — static routes (e.g. `/patients/resources`) must be registered before dynamic ones (`/patients/{id}`). At startup, `main.py` also runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` migrations for `ai_analysis JSONB` on `cluster_meta`, `cluster`, and `prefix_span_pattern`, plus `pca_image BYTEA` on `cluster_meta`.

**Database**: SQLModel ORM + raw `text()` queries. `db/db_connector.py` exposes `engine`, `SessionLocal`, `get_db()` (FastAPI dependency), and `_db_retrieve(query_text)` (raw query → list of dicts). Dynamic WHERE clauses are built by appending to a `conditions: list[str]` and `params: dict`, then joined with `AND`. `cluster_meta` is a singleton table (one row) holding the current clustering run's metadata; re-runs TRUNCATE and re-INSERT. Load raw data with `db/etl_script.py`.

**Clustering**: `clustering_algorithms/k_prototypes/k_prototypes.py` is a **standalone script** (run directly with `python k_prototypes.py` from its directory, not via FastAPI). It builds patient features, runs k-prototypes, calls the LLM for cluster summaries, and persists results via `save_results.py`. Results stored in `cluster_meta`, `cluster`, and `cluster_patient` tables. The `cluster_patient.features` JSONB column caches per-patient computed features for fast summary retrieval.

**LLM SQL Agent**: `service/lllm_sql_agent_service/` (three l's) uses LangGraph + Google GenAI / OpenAI to translate natural language queries into SQL. Exposed via `statistics_router`.
