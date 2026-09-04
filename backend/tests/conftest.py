"""Shared test fixtures: an isolated in-memory SQLite DB and dependency overrides.

Each test gets a fresh database. ``client`` wires that DB into the app via
``get_db``; ``make_user`` seeds a user; ``as_user`` pins ``get_current_user`` to a
given user so auth'd endpoints can be exercised without a real login round-trip.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import get_current_user
from app.core.db import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User


@pytest.fixture
def db_session() -> Session:
    """A fresh in-memory SQLite session, shared between the test body and the app."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one connection for the whole test => schema/data persist
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """TestClient with ``get_db`` overridden to the test session (no lifespan -> no model load)."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session: Session):
    """Factory that inserts a ``User`` row and returns it."""

    def _make_user(
        email: str = "user@example.com", password: str = "correct horse battery"
    ) -> User:
        user = User(email=email, hashed_password=hash_password(password))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def as_user():
    """Pin ``get_current_user`` to a specific user for the duration of the test."""

    def _as_user(user: User) -> None:
        app.dependency_overrides[get_current_user] = lambda: user

    return _as_user
