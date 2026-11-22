"""Database engine, session factory and declarative base."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

SQLITE_PREFIX = "sqlite:///"


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_directory(url: str) -> None:
    """Create the parent directory of a relative SQLite file path before the engine opens it.

    The path is relative to the current working directory (the backend folder when uvicorn runs there).
    """
    if url.startswith(SQLITE_PREFIX):
        db_path = url[len(SQLITE_PREFIX):]
        if db_path and db_path != ":memory:":
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)


_settings = get_settings()
_ensure_sqlite_directory(_settings.database_url)

engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
