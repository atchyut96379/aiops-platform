from fastapi import FastAPI

app = FastAPI(
    title="AIOps Platform",
    description="Enterprise AI Operations Platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to AIOps Platform",
        "status": "Running Successfully"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }