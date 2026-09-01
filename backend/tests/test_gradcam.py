"""Unit tests for the Grad-CAM helper (runs against an untrained model)."""

import base64
import io

import numpy as np
import pytest
from PIL import Image

from app.ml.gradcam import compute_cam, overlay_data_uri, render_overlay
from app.ml.model import build_model, preprocess


@pytest.fixture(scope="module")
def model():
    return build_model()


def test_compute_cam_shape_and_range(model):
    cam = compute_cam(model, preprocess(Image.new("L", (64, 64), 128)))

    assert cam.shape == (12, 12)  # last conv layer's spatial size for this CNN
    assert np.isfinite(cam).all()
    assert 0.0 <= float(cam.min()) and float(cam.max()) <= 1.0 + 1e-6


def test_render_overlay_matches_original_size(model):
    original = Image.new("L", (211, 173), 90)  # odd, non-square, grayscale
    cam = compute_cam(model, preprocess(original))

    overlay = render_overlay(original, cam)

    assert overlay.size == original.size
    assert overlay.mode == "RGB"


def test_overlay_data_uri_is_a_jpeg(model):
    original = Image.new("RGB", (128, 96), "white")
    uri = overlay_data_uri(model, preprocess(original), original)

    assert uri.startswith("data:image/jpeg;base64,")
    decoded = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))
    assert decoded.format == "JPEG"
    assert decoded.size == original.size
