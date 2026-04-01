from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy import text

from app import statistics_router, cluster_router, patient_router
from db.db_connector import engine
import domain.models  # noqa: F401 - ensures all models are registered before create_all

routers = [
    statistics_router,
    cluster_router,
    patient_router,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE cluster_run ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.execute(text("ALTER TABLE cluster ADD COLUMN IF NOT EXISTS ai_analysis JSONB"))
            conn.commit()
    except Exception:
        pass  # tables may not exist yet; clustering script will create them
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
