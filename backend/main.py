from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, http_exception_handler
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter
from app.db import base  # noqa: F401 — register models
from app.db.database import Base, SessionLocal, engine
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.role import ensure_system_roles

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_system_roles(db)
        logger.info("System roles seeded")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "Enterprise AI Operations Platform API. "
        "Module 01: Authentication, users, organizations, and RBAC foundation."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)


@app.get("/", tags=["System"])
def home() -> dict:
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "healthy", "environment": settings.APP_ENV}


@app.get("/db-test", tags=["System"])
def db_test() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as exc:  # noqa: BLE001 — surface connection errors to ops
        return {"database": "connection_failed", "error": str(exc)}
