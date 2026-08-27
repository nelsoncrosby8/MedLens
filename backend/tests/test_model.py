"""Tests for the pneumonia-classifier inference module.

The architecture/plumbing tests run against a freshly built (untrained) model, so the
suite is green before ``export_weights.py`` has ever been run. The one test that needs
real trained weights is skipped until the weights file exists.
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.ml import model as model_module
from app.ml.model import DEFAULT_WEIGHTS_PATH, build_model, load_model, predict, preprocess

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def normal_image() -> Image.Image:
    return Image.open(DATA_DIR / "normal_sample.jpeg")


@pytest.fixture(scope="module")
def pneumonia_image() -> Image.Image:
    return Image.open(DATA_DIR / "pneumonia_sample.jpeg")


def test_preprocess_shape_and_range():
    # Odd, non-square, single-channel input to exercise the convert/resize path.
    raw = Image.new("L", (500, 400), color=128)
    batch = preprocess(raw)

    assert batch.shape == (1, 64, 64, 3)
    assert batch.dtype == np.float32
    assert 0.0 <= float(batch.min()) and float(batch.max()) <= 1.0


def test_predict_contract_untrained(normal_image):
    # An untrained model still produces a valid, well-formed prediction.
    result = predict(normal_image, model=build_model())

    assert result["label"] in {"NORMAL", "PNEUMONIA"}
    assert 0.0 <= result["probability"] <= 1.0
    # probability is P(PNEUMONIA); label must agree with the 0.5 threshold.
    assert (result["label"] == "PNEUMONIA") == (result["probability"] > 0.5)


def test_predict_singleton_not_required_when_model_passed(pneumonia_image, monkeypatch):
    # Passing an explicit model must never touch the (absent) weights singleton.
    monkeypatch.setattr(model_module, "_MODEL", None)
    predict(pneumonia_image, model=build_model())
    assert model_module._MODEL is None


@pytest.mark.skipif(
    not DEFAULT_WEIGHTS_PATH.is_file(),
    reason="trained weights not present — run `python -m app.ml.export_weights` first",
)
def test_predict_pneumonia_sample(pneumonia_image):
    result = predict(pneumonia_image, model=load_model())

    assert result["label"] == "PNEUMONIA"
    assert result["probability"] > 0.5
