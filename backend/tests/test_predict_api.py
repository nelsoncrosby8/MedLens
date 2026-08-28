"""API tests for /health and /predict using FastAPI's TestClient.

``app.main.load_model`` is monkeypatched to hand back an *untrained* model, so the
whole real request path (lifespan -> app.state -> get_model dependency -> inference)
is exercised without depending on a trained weights file. One extra test uses the
real weights when they happen to be present.
"""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.ml.model import DEFAULT_WEIGHTS_PATH, build_model

DATA_DIR = Path(__file__).parent / "data"
PNEUMONIA_SAMPLE = DATA_DIR / "pneumonia_sample.jpeg"


@pytest.fixture(scope="module")
def untrained_model():
    return build_model()


@pytest.fixture
def client(monkeypatch, untrained_model):
    monkeypatch.setattr("app.main.load_model", lambda *args, **kwargs: untrained_model)
    with TestClient(app) as test_client:
        yield test_client


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_valid_image_returns_200(client):
    with PNEUMONIA_SAMPLE.open("rb") as fh:
        response = client.post(
            "/predict", files={"file": ("xray.jpeg", fh, "image/jpeg")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["label"] in {"NORMAL", "PNEUMONIA"}
    assert 0.0 <= body["probability"] <= 1.0


def test_predict_accepts_generated_png(client):
    # A different format/mode than the JPEG sample, built in memory.
    buf = io.BytesIO()
    Image.new("L", (128, 96), color=90).save(buf, format="PNG")
    response = client.post(
        "/predict", files={"file": ("synthetic.png", buf.getvalue(), "image/png")}
    )

    assert response.status_code == 200
    assert response.json()["label"] in {"NORMAL", "PNEUMONIA"}


def test_predict_non_image_returns_400(client):
    response = client.post(
        "/predict", files={"file": ("notes.txt", b"this is not an image", "text/plain")}
    )
    assert response.status_code == 400


def test_predict_corrupt_image_bytes_returns_400(client):
    # Declared as an image, but the bytes don't decode.
    response = client.post(
        "/predict", files={"file": ("fake.png", b"\x89PNG\r\n\x1a\n garbage", "image/png")}
    )
    assert response.status_code == 400


def test_predict_oversized_file_returns_413(client):
    oversized = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 1)
    response = client.post(
        "/predict", files={"file": ("big.png", oversized, "image/png")}
    )
    assert response.status_code == 413


@pytest.mark.skipif(
    not DEFAULT_WEIGHTS_PATH.is_file(),
    reason="trained weights not present — run `python -m app.ml.export_weights` first",
)
def test_predict_with_real_weights_classifies_pneumonia():
    # No monkeypatch here: real lifespan, real load_model(), real weights.
    with TestClient(app) as real_client:
        with PNEUMONIA_SAMPLE.open("rb") as fh:
            response = real_client.post(
                "/predict", files={"file": ("xray.jpeg", fh, "image/jpeg")}
            )

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "PNEUMONIA"
    assert body["probability"] > 0.5
