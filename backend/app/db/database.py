from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


connect_args: dict[str, Any] = {}
if settings.is_sqlite:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    connect_args=connect_args,
    pool_pre_ping=not settings.is_sqlite,
)

if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
