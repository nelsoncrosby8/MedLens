"""Auth API tests (signup / login / JWT-protected route).

Runs against a fresh in-memory SQLite database per test — isolated from dev data and
fast. ``get_db`` is overridden; ``TestClient(app)`` is used without the ``with`` block so
the model-loading lifespan never runs (these tests don't touch the CNN).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app

SIGNUP = {"email": "alice@example.com", "password": "correct horse battery"}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection => schema persists for the test
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _token(client) -> str:
    client.post("/auth/signup", json=SIGNUP)
    resp = client.post(
        "/auth/login",
        data={"username": SIGNUP["email"], "password": SIGNUP["password"]},
    )
    return resp.json()["access_token"]


def test_signup_success(client):
    resp = client.post("/auth/signup", json=SIGNUP)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == SIGNUP["email"]
    assert isinstance(body["id"], int)
    assert "hashed_password" not in body and "password" not in body


def test_signup_duplicate_email_returns_400(client):
    assert client.post("/auth/signup", json=SIGNUP).status_code == 201

    resp = client.post("/auth/signup", json=SIGNUP)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_success_returns_bearer_token(client):
    client.post("/auth/signup", json=SIGNUP)

    resp = client.post(
        "/auth/login",
        data={"username": SIGNUP["email"], "password": SIGNUP["password"]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_returns_401(client):
    client.post("/auth/signup", json=SIGNUP)

    resp = client.post(
        "/auth/login",
        data={"username": SIGNUP["email"], "password": "not my password"},
    )
    assert resp.status_code == 401


def test_me_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer notajwt"})
    assert resp.status_code == 401


def test_me_with_valid_token_returns_user(client):
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {_token(client)}"})

    assert resp.status_code == 200
    assert resp.json()["email"] == SIGNUP["email"]
