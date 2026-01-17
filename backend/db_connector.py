import pandas as pd
from sqlalchemy import create_engine

url = create_engine("postgres://postgres:postgres@localhost:5432/postgres")



pd.read_csv