import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy import text

from app import statistics_router, cluster_router, patient_router, provider_router, dashboard_router, encounter_router, sequence_router, auth_router
from db.db_connector import engine
from messaging import startup_messaging, shutdown_messaging
import domain.models  # noqa: F401 - ensures all models are registered before create_all

logger = logging.getLogger(__name__)

# Microservices deployment: a single codebase deployed N times. SERVICE_NAME
# selects which routers this container exposes. Default ("monolith") keeps the
# legacy behaviour for `uvicorn` invocation outside docker-compose.
SERVICE_ROUTERS = {
    "monolith": [statistics_router, cluster_router, sequence_router, patient_router,
                 provider_router, dashboard_router, encounter_router, auth_router],
    "auth": [auth_router],
    "users": [],  # placeholder; user CRUD endpoints land here
    "clinical-core": [patient_router, provider_router, encounter_router],
    "analytics": [statistics_router, dashboard_router],
    "ml-batch": [cluster_router, sequence_router],
    "mail-service": [],
    "queue-service": [],
}

SERVICE_NAME = os.getenv("SERVICE_NAME", "monolith")
routers = SERVICE_ROUTERS.get(SERVICE_NAME, SERVICE_ROUTERS["monolith"])


def _default_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


RUN_CLINICAL_MIGRATIONS = SERVICE_NAME in ("monolith", "clinical-core")
RUN_ML_MIGRATIONS = SERVICE_NAME in ("monolith", "ml-batch")
RUN_MESSAGING = SERVICE_NAME in ("monolith", "clinical-core", "mail-service", "ml-batch", "queue-service", "auth", "analytics")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Per-service table creation: each service's primary DB only contains
    # the tables it owns. The model registry knows the mapping.
    from db.model_registry import tables_for
    owned = tables_for(SERVICE_NAME)
    if owned:
        try:
            SQLModel.metadata.create_all(engine, tables=owned)
        except Exception:
            logger.exception("create_all failed for service=%s", SERVICE_NAME)

    sync_tasks = []

    async def _start_sync_consumers():
        import asyncio as _asyncio
        if SERVICE_NAME in ("auth", "monolith"):
            from sync.account_consumer import AccountSyncConsumer
            sync_tasks.append(_asyncio.create_task(AccountSyncConsumer().run()))
            logger.info("started AccountSyncConsumer")
        if SERVICE_NAME in ("ml-batch", "monolith"):
            from sync.ml_consumer import MlSyncConsumer
            sync_tasks.append(_asyncio.create_task(MlSyncConsumer().run()))
            logger.info("started MlSyncConsumer")
        if SERVICE_NAME == "mail-service":
            from sync.mail_consumer import MailConsumer
            sync_tasks.append(_asyncio.create_task(MailConsumer().run()))
            logger.info("started MailConsumer")

    async def _stop_sync_consumers():
        for t in sync_tasks:
            t.cancel()

    if not RUN_CLINICAL_MIGRATIONS and not RUN_ML_MIGRATIONS:
        if RUN_MESSAGING:
            await startup_messaging()
        await _start_sync_consumers()
        try:
            yield
        finally:
            await _stop_sync_consumers()
            if RUN_MESSAGING:
                await shutdown_messaging()
        return

    if RUN_CLINICAL_MIGRATIONS:
        try:
            with engine.connect() as conn:
                # pg_trgm extension + GIN indexes for ILIKE '%pattern%' queries
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_obs_desc_trgm ON observation USING GIN(description gin_trgm_ops)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cond_desc_trgm ON condition USING GIN(description gin_trgm_ops)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observation_description ON observation (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observation_value_numeric ON observation (value_numeric)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_condition_description ON condition (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_medication_description ON medication (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_procedure_description ON procedure (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_immunization_description ON immunization (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_allergy_description ON allergy (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_careplan_description ON careplan (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_description ON encounter (description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_reason_description ON encounter (reason_description)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_class ON encounter (encounter_class)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_provider_organization_id ON provider (organization_id)"))
                conn.commit()
        except Exception:
            logger.exception("clinical-core startup migrations failed")

    if RUN_ML_MIGRATIONS:
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS pca_image BYTEA"))
                conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
                conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS detail_cache JSONB"))
                conn.execute(text("ALTER TABLE prefix_span_pattern ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
                # ml_db has no `patient` table - cross-DB FK was removed; integrity is
                # enforced at the application layer + via patient.deleted events.
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_label ON cluster (cluster_label)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_label ON cluster_patient (cluster_label)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_outlier ON cluster_patient (is_outlier)"))
                conn.commit()
        except Exception:
            logger.exception("ml-batch startup migrations failed")

    # Observation materialized views - pre-aggregate millions of rows so the
    # statistics endpoint responds in milliseconds. They live in clinical_db
    # alongside the source `observation` table; analytics reads them via the
    # clinical-read engine.
    if not RUN_CLINICAL_MIGRATIONS:
        if RUN_MESSAGING:
            await startup_messaging()
        await _start_sync_consumers()
        try:
            yield
        finally:
            await _stop_sync_consumers()
            if RUN_MESSAGING:
                await shutdown_messaging()
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_obs_totals AS
                SELECT
                    count(*)                             AS total_observations,
                    count(DISTINCT observation_code)     AS unique_types,
                    count(DISTINCT patient_id)           AS total_patients
                FROM observation
            """))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_obs_per_patient AS
                SELECT
                    round(cast(avg(cnt) AS numeric), 2)  AS avg_cnt,
                    min(cnt)                             AS min_cnt,
                    max(cnt)                             AS max_cnt
                FROM (
                    SELECT patient_id, count(*) AS cnt
                    FROM observation
                    GROUP BY patient_id
                ) t
            """))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_obs_top_types AS
                SELECT description, count(*) AS cnt
                FROM observation
                GROUP BY description
                ORDER BY cnt DESC
            """))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_obs_numeric_stats AS
                SELECT
                    description,
                    units,
                    count(*)                                                    AS cnt,
                    count(DISTINCT patient_id)                                  AS patient_count,
                    round(cast(min(value_numeric) AS numeric), 2)               AS min_val,
                    round(cast(max(value_numeric) AS numeric), 2)               AS max_val,
                    round(cast(avg(value_numeric) AS numeric), 2)               AS avg_val
                FROM observation
                WHERE value_numeric IS NOT NULL
                GROUP BY description, units
            """))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_obs_categorical_stats AS
                SELECT
                    description,
                    count(*)                        AS cnt,
                    count(DISTINCT patient_id)      AS patient_count,
                    count(DISTINCT value)           AS distinct_values
                FROM observation
                WHERE value_numeric IS NULL
                  AND value IS NOT NULL
                  AND value != ''
                GROUP BY description
            """))
            conn.commit()
    except Exception:
        logger.exception("Observation materialized view creation failed")

    if RUN_MESSAGING:
        await startup_messaging()
    await _start_sync_consumers()
    try:
        yield
    finally:
        await _stop_sync_consumers()
        if RUN_MESSAGING:
            await shutdown_messaging()


app = FastAPI(lifespan=lifespan, title=f"hospital-analytics:{SERVICE_NAME}")

for router in routers:
    app.include_router(router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": SERVICE_NAME}


app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
