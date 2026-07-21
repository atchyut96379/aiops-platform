import os
from collections.abc import Generator

# Configure test env before application imports
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-aiops-123456"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["APP_ENV"] = "test"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["EMAIL_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
import app.core.config as config_module
import app.db.database as database_module
from app.db.database import Base, get_db
from app.services.role import ensure_system_roles

get_settings.cache_clear()
config_module.settings = get_settings()

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Point the application DB layer at the shared in-memory engine
database_module.engine = engine
database_module.SessionLocal = TestingSessionLocal
database_module.settings = config_module.settings


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        ensure_system_roles(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from main import app

    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
