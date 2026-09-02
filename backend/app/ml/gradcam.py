"""Grad-CAM for the custom CNN.

Highlights the regions of a chest X-ray that most drove the pneumonia score and
returns them blended over the original image as a base64 JPEG ``data:`` URI (so the
frontend can drop it straight into an ``<img>``). The overlay is a visualisation,
not diagnostic data, so lossy JPEG keeps the response small.
"""

from __future__ import annotations

import base64
import io

import matplotlib
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow import keras

_COLORMAP = matplotlib.colormaps["jet"]
_MAX_OVERLAY_ALPHA = 0.45  # opacity of the heat colour where the CAM is hottest
_CONTRAST_GAMMA = 2.0  # >1 suppresses mid activations so the peaks stand out
_MAX_OVERLAY_SIDE = 1024  # cap the overlay's longest side to keep the data URI small


def _last_conv_layer(model: keras.Model) -> keras.layers.Layer:
    for layer in reversed(model.layers):
        if isinstance(layer, keras.layers.Conv2D):
            return layer
    raise ValueError("model has no Conv2D layer for Grad-CAM")


def compute_cam(model: keras.Model, batch: np.ndarray) -> np.ndarray:
    """Return a normalised (0-1) Grad-CAM map for the one image in ``batch``.

    ``batch`` is the preprocessed model input, shape ``(1, H, W, 3)``. The result's
    shape is the last convolutional layer's spatial size (12x12 for this CNN).
    """
    last_conv = _last_conv_layer(model)
    grad_model = keras.Model(model.inputs, [last_conv.output, model.output])

    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(batch)
        score = preds[:, 0]  # the single sigmoid unit == P(PNEUMONIA)

    grads = tape.gradient(score, conv_out)  # (1, h, w, C)
    weights = tf.reduce_mean(grads, axis=(1, 2))  # (1, C): how much each feature map matters
    cam = tf.reduce_sum(conv_out[0] * weights[0], axis=-1)  # (h, w) weighted sum of maps
    cam = tf.nn.relu(cam)  # keep only regions that push the score up
    # Min-max normalise so the coldest region is fully transparent in the overlay
    # (plain max-normalising leaves a global colour wash when the CAM floor is high),
    # then gamma-compress to pull mid activations down toward zero.
    cam = cam - tf.reduce_min(cam)
    cam = cam / (tf.reduce_max(cam) + 1e-8)  # -> [0, 1]
    cam = cam**_CONTRAST_GAMMA
    return cam.numpy()


def render_overlay(original: Image.Image, cam: np.ndarray) -> Image.Image:
    """Blend the colour-mapped CAM over ``original``, weighted by CAM strength.

    Cold regions show the X-ray almost untouched; hot regions get the jet colour.
    """
    display = original.convert("RGB")
    if max(display.size) > _MAX_OVERLAY_SIDE:
        scale = _MAX_OVERLAY_SIDE / max(display.size)
        display = display.resize(
            (round(display.width * scale), round(display.height * scale)), Image.BILINEAR
        )

    base = np.asarray(display, dtype=np.float32)
    height, width = base.shape[:2]

    cam_img = Image.fromarray((cam * 255).astype("uint8")).resize((width, height), Image.BILINEAR)
    cam_resized = np.asarray(cam_img, dtype=np.float32) / 255.0  # (h, w) in [0, 1]

    heat = _COLORMAP(cam_resized)[..., :3] * 255.0  # (h, w, 3) — drop the alpha channel
    alpha = (cam_resized * _MAX_OVERLAY_ALPHA)[..., None]
    blended = base * (1.0 - alpha) + heat * alpha
    return Image.fromarray(np.clip(blended, 0, 255).astype("uint8"))


def overlay_data_uri(model: keras.Model, batch: np.ndarray, original: Image.Image) -> str:
    """Grad-CAM overlay for ``original`` as a ``data:image/jpeg;base64,...`` string."""
    overlay = render_overlay(original, compute_cam(model, batch))
    buffer = io.BytesIO()
    overlay.save(buffer, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
