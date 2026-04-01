import os
import logging
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

PG_USERNAME = os.getenv("POSTGRES_USERNAME")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_HOST = os.getenv("POSTGRES_HOST")
PG_PORT = os.getenv("POSTGRES_PORT")
PG_DATABASE = os.getenv("POSTGRES_DB")

url = URL.create(
    drivername="postgresql+psycopg2",
    username=PG_USERNAME,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE,
)

engine = create_engine(url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _db_retrieve(query_text: str) -> list[dict]:
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query_text))
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Query failed: {e}\nSQL: {query_text}")
        raise e