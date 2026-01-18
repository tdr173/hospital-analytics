from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app import get_db

app = FastAPI()


@app.get("/")
async def root(db: Session = Depends(get_db)):
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
