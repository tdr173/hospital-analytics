import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app import users_router
from db.db_connector import engine
from messaging import startup_messaging, shutdown_messaging
import domain.models  # noqa: F401 - ensures all models are registered before create_all

logger = logging.getLogger(__name__)

# Microservices deployment: a single codebase deployed N times. SERVICE_NAME
# selects which routers this container exposes. Default ("monolith") keeps the
# legacy behaviour for `uvicorn` invocation outside docker-compose.
SERVICE_ROUTERS = {
    "users": [users_router],
}

SERVICE_NAME = os.getenv("SERVICE_NAME", "users")
routers = SERVICE_ROUTERS.get(SERVICE_NAME, [users_router])


def _default_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


RUN_MESSAGING = True


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
        from sync.user_consumer import UserSyncConsumer
        sync_tasks.append(_asyncio.create_task(UserSyncConsumer().run()))
        logger.info("started UserSyncConsumer")

    async def _stop_sync_consumers():
        for t in sync_tasks:
            t.cancel()

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
