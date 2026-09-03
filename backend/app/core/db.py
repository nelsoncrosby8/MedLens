"""SQLAlchemy engine, session factory, declarative base, and the per-request session."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

# check_same_thread only matters for SQLite (used by the test suite); harmless to compute here.
_connect_args = {"check_same_thread": False} if _settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,  # drop dead connections instead of erroring mid-request
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a session for one request, always closing it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
