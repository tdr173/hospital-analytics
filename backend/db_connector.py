from sqlalchemy import create_engine

url = create_engine("postgres://postgres:postgres@localhost:5432/postgres")