import logging
import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy import text

from app import statistics_router, cluster_router, patient_router, provider_router, dashboard_router, encounter_router, sequence_router
from db.db_connector import engine, SessionLocal
import domain.models  # noqa: F401 - ensures all models are registered before create_all

logger = logging.getLogger(__name__)

routers = [
    statistics_router,
    cluster_router,
    sequence_router,
    patient_router,
    provider_router,
    dashboard_router,
    encounter_router,
]


def _warm_cluster_detail_cache() -> None:
    """Precompute cluster detail_cache in the background so the first
    /clusters/detail load doesn't pay the ~minute-long observation scans."""
    from repository import ClusterRepository
    from service import ClusterService

    try:
        with SessionLocal() as db:
            service = ClusterService(ClusterRepository(db))
            warmed = service.warm_detail_cache()
        if warmed:
            logger.info("Warmed cluster detail_cache for labels: %s", warmed)
    except Exception:
        logger.exception("Background cluster detail_cache warm-up failed")


def _default_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS pca_image BYTEA"))
            conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS detail_cache JSONB"))
            conn.execute(text("ALTER TABLE prefix_span_pattern ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE prefix_span_pattern ADD COLUMN IF NOT EXISTS cluster_label INT NULL"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_prefix_span_pattern_cluster_label ON prefix_span_pattern (cluster_label)"))
            # NOT VALID skips the check on existing rows; new inserts are still validated.
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'fk_cluster_patient_patient_id'
                    ) THEN
                        ALTER TABLE cluster_patient
                        ADD CONSTRAINT fk_cluster_patient_patient_id
                        FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
                        NOT VALID;
                    END IF;
                END;
                $$;
            """))
            # pg_trgm extension + GIN indexes for ILIKE '%pattern%' queries
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_obs_desc_trgm ON observation USING GIN(description gin_trgm_ops)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cond_desc_trgm ON condition USING GIN(description gin_trgm_ops)"))
            # observation indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observation_description ON observation (description)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_observation_value_numeric ON observation (value_numeric)"))
            # condition indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_condition_description ON condition (description)"))
            # medication indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_medication_description ON medication (description)"))
            # procedure indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_procedure_description ON procedure (description)"))
            # immunization indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_immunization_description ON immunization (description)"))
            # allergy indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_allergy_description ON allergy (description)"))
            # careplan indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_careplan_description ON careplan (description)"))
            # encounter indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_description ON encounter (description)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_reason_description ON encounter (reason_description)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_class ON encounter (encounter_class)"))
            # start_date indexes - the dashboard KPI query filters every big table
            # by `start_date >= cutoff`; without these it seq-scans encounter (1.2M),
            # condition (727k) and procedure (3.2M) on every range != "all" request.
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_encounter_start_date ON encounter (start_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_condition_start_date ON condition (start_date)"))
            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_procedure_start_date ON "procedure" (start_date)'))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_careplan_start_date ON careplan (start_date)"))
            # cluster indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_label ON cluster (cluster_label)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_label ON cluster_patient (cluster_label)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_outlier ON cluster_patient (is_outlier)"))
            # provider indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_provider_organization_id ON provider (organization_id)"))
            conn.commit()
    except Exception:
        logger.exception("Startup migrations failed - some ALTER/INDEX/CONSTRAINT statements did not run")

    # Observation materialized views - pre-aggregate millions of rows so the
    # statistics endpoint responds in milliseconds instead of ~30 seconds.
    # IF NOT EXISTS makes this a no-op on every restart after the first build.
    # Re-run manually after ETL: REFRESH MATERIALIZED VIEW <view_name>;
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

    # Warm the per-cluster detail cache in a daemon thread so startup is not
    # blocked. New/uncached clusters get precomputed; cached ones are skipped.
    threading.Thread(
        target=_warm_cluster_detail_cache,
        name="warm-cluster-detail-cache",
        daemon=True,
    ).start()

    yield


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
