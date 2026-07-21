from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import Base,engine
from app.db import base 

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIOps Platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "Welcome to AIOps Platform"}


@app.get("/health")
def health():
    return {"status": "Healthy"}


@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "Connected Successfully"}
    except Exception as e:
        return {"database": "Connection Failed", "error": str(e)}