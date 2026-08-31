"""CORS is enabled so the browser frontend (another origin) can call the API."""

from app.main import app
from fastapi.testclient import TestClient

ORIGIN = "http://localhost:5173"


def test_cors_preflight_allows_frontend_origin():
    response = TestClient(app).options(
        "/predict",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
