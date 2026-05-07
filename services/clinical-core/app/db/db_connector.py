"""Per-service database connector.

Each microservice has its own primary Postgres. Read-only services that
need data living in another service's DB (analytics, ml-batch, the LLM SQL
agent) get explicit read engines configured via env vars.

Environment variables read here:
  POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
      — primary (writable) DB for this service.
  CLINICAL_DB_HOST/PORT/USER/PASSWORD/NAME (optional)
      — read connection to clinical_db. Set on analytics + ml-batch.
  ML_DB_HOST/PORT/USER/PASSWORD/NAME (optional)
      — read connection to ml_db. Set on analytics (for the SQL agent).
  AUTH_DB_HOST/PORT/USER/PASSWORD/NAME (optional)
      — read connection to auth_db. Rarely needed; left here for completeness.
"""
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

logger = logging.getLogger(__name__)


def _build_url(user_env: str, pass_env: str, host_env: str, port_env: str, db_env: str):
    user = os.getenv(user_env)
    password = os.getenv(pass_env)
    host = os.getenv(host_env)
    port = os.getenv(port_env)
    database = os.getenv(db_env)
    if not (user and password and host and port and database):
        return None
    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


# ---------- primary engine (writable) ----------
url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("POSTGRES_USERNAME"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    database=os.getenv("POSTGRES_DB"),
)
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _db_retrieve(db: Session, query_text: str) -> list[dict]:
    try:
        result = db.execute(text(query_text))
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Query failed: {e}\nSQL: {query_text}")
        raise


# ---------- secondary read-only engines (cross-service) ----------
_clinical_url = _build_url("CLINICAL_DB_USER", "CLINICAL_DB_PASSWORD",
                           "CLINICAL_DB_HOST", "CLINICAL_DB_PORT", "CLINICAL_DB_NAME")
_ml_url = _build_url("ML_DB_USER", "ML_DB_PASSWORD",
                     "ML_DB_HOST", "ML_DB_PORT", "ML_DB_NAME")
_auth_url = _build_url("AUTH_DB_USER", "AUTH_DB_PASSWORD",
                       "AUTH_DB_HOST", "AUTH_DB_PORT", "AUTH_DB_NAME")

clinical_read_engine = create_engine(_clinical_url, pool_pre_ping=True) if _clinical_url else None
ml_read_engine = create_engine(_ml_url, pool_pre_ping=True) if _ml_url else None
auth_read_engine = create_engine(_auth_url, pool_pre_ping=True) if _auth_url else None


def read_engine(name: str):
    """Look up a read-only engine by short name. Returns None if not configured."""
    return {
        "clinical": clinical_read_engine,
        "ml": ml_read_engine,
        "auth": auth_read_engine,
    }.get(name)
