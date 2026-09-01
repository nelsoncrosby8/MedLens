"""Auth API tests (signup / login / JWT-protected route).

Uses the shared ``client`` fixture (fresh in-memory SQLite, ``get_db`` overridden).
"""

SIGNUP = {"email": "alice@example.com", "password": "correct horse battery"}


def _login_token(client) -> str:
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
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {_login_token(client)}"})

    assert resp.status_code == 200
    assert resp.json()["email"] == SIGNUP["email"]
