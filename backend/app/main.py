from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy import text

from app import statistics_router, cluster_router, patient_router, provider_router, organization_router, dashboard_router, encounter_router, sequence_router
from db.db_connector import engine
import domain.models  # noqa: F401 - ensures all models are registered before create_all

routers = [
    statistics_router,
    cluster_router,
    sequence_router,
    patient_router,
    provider_router,
    organization_router,
    dashboard_router,
    encounter_router,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE prefix_span_pattern ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
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
            # cluster indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_label ON cluster (cluster_label)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_label ON cluster_patient (cluster_label)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cluster_patient_outlier ON cluster_patient (is_outlier)"))
            # provider indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_provider_organization_id ON provider (organization_id)"))
            conn.commit()
    except Exception:
        pass  # tables may not exist yet on first boot

    # Observation materialized views — pre-aggregate millions of rows so the
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
        pass  # view creation silently skipped if observation table not yet populated

    yield


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
