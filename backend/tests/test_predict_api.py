"""API tests for /health and /predict.

/predict now requires auth and persists each result, so these use the shared DB
fixtures (in-memory SQLite) plus a fast untrained model via ``override_model``. One
test opts into the real trained weights when the file is present.
"""

import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from app.api.predict import get_model
from app.main import app
from app.ml.model import DEFAULT_WEIGHTS_PATH, build_model, load_model
from app.models.prediction import Prediction

DATA_DIR = Path(__file__).parent / "data"
PNEUMONIA_SAMPLE = DATA_DIR / "pneumonia_sample.jpeg"

_UNTRAINED_MODEL = None


def _assert_jpeg_data_uri(value: str) -> None:
    assert value.startswith("data:image/jpeg;base64,")
    decoded = Image.open(io.BytesIO(base64.b64decode(value.split(",", 1)[1])))
    assert decoded.format == "JPEG"


@pytest.fixture
def override_model():
    """Point /predict at a cached untrained model (no weights file needed)."""
    global _UNTRAINED_MODEL
    if _UNTRAINED_MODEL is None:
        _UNTRAINED_MODEL = build_model()
    app.dependency_overrides[get_model] = lambda: _UNTRAINED_MODEL
    yield
    app.dependency_overrides.pop(get_model, None)


@pytest.fixture
def auth_client(client, override_model, make_user, as_user):
    """A TestClient with an untrained model and a signed-in user."""
    as_user(make_user())
    return client


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_requires_auth(client, override_model):
    with PNEUMONIA_SAMPLE.open("rb") as fh:
        response = client.post("/predict", files={"file": ("xray.jpeg", fh, "image/jpeg")})
    assert response.status_code == 401


def test_predict_valid_image_returns_200_and_persists(auth_client, db_session):
    with PNEUMONIA_SAMPLE.open("rb") as fh:
        response = auth_client.post(
            "/predict", files={"file": ("xray.jpeg", fh, "image/jpeg")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["label"] in {"NORMAL", "PNEUMONIA"}
    assert 0.0 <= body["probability"] <= 1.0
    assert isinstance(body["id"], int)
    assert body["created_at"]
    _assert_jpeg_data_uri(body["heatmap"])

    rows = db_session.query(Prediction).all()
    assert len(rows) == 1
    assert rows[0].id == body["id"]
    assert rows[0].label == body["label"]
    assert rows[0].filename == "xray.jpeg"


def test_predict_accepts_generated_png(auth_client):
    buf = io.BytesIO()
    Image.new("L", (128, 96), color=90).save(buf, format="PNG")
    response = auth_client.post(
        "/predict", files={"file": ("synthetic.png", buf.getvalue(), "image/png")}
    )

    assert response.status_code == 200
    assert response.json()["label"] in {"NORMAL", "PNEUMONIA"}


def test_predict_non_image_returns_400(auth_client):
    response = auth_client.post(
        "/predict", files={"file": ("notes.txt", b"this is not an image", "text/plain")}
    )
    assert response.status_code == 400


def test_predict_corrupt_image_bytes_returns_400(auth_client):
    response = auth_client.post(
        "/predict", files={"file": ("fake.png", b"\x89PNG\r\n\x1a\n garbage", "image/png")}
    )
    assert response.status_code == 400


def test_predict_oversized_file_returns_413(auth_client):
    oversized = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 1)
    response = auth_client.post(
        "/predict", files={"file": ("big.png", oversized, "image/png")}
    )
    assert response.status_code == 413


@pytest.mark.skipif(
    not DEFAULT_WEIGHTS_PATH.is_file(),
    reason="trained weights not present — run `python -m app.ml.export_weights` first",
)
def test_predict_with_real_weights_classifies_pneumonia(client, db_session, make_user, as_user):
    as_user(make_user())
    real_model = load_model()
    app.dependency_overrides[get_model] = lambda: real_model
    try:
        with PNEUMONIA_SAMPLE.open("rb") as fh:
            response = client.post(
                "/predict", files={"file": ("xray.jpeg", fh, "image/jpeg")}
            )
    finally:
        app.dependency_overrides.pop(get_model, None)

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "PNEUMONIA"
    assert body["probability"] > 0.5
    _assert_jpeg_data_uri(body["heatmap"])
    assert db_session.query(Prediction).count() == 1
