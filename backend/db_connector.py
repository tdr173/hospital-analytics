import os
import pandas as pd
from dotenv import load_dotenv

from sqlalchemy import URL, create_engine, MetaData

load_dotenv()

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

engine = create_engine(url)



