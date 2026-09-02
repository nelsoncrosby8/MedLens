"""Inference for the MedLens pneumonia classifier.

This module is a faithful port of the *custom CNN* from the development notebook
(``notebooks/pneumonia_classifier.ipynb``). It rebuilds the exact architecture and
loads trained weights produced by ``export_weights.py``. There is deliberately **no
training code here** — the model file is treated as a black box per project conventions.

Contract carried over from the notebook:
  * input: RGB image resized to 64x64, pixels scaled to [0, 1] (``rescale=1./255``)
  * output: a single sigmoid unit = P(PNEUMONIA)
  * label mapping (alphabetical, ``class_mode="binary"``): NORMAL = 0, PNEUMONIA = 1
  * decision rule: ``sigmoid > 0.5`` -> PNEUMONIA
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image
from tensorflow import keras

# --- Constants mirroring the notebook -----------------------------------------

CLASS_NAMES: list[str] = ["NORMAL", "PNEUMONIA"]  # index 0 / 1, matches training
INPUT_SIZE: tuple[int, int] = (64, 64)  # (width, height) fed to the network
DECISION_THRESHOLD: float = 0.5

# Weights are not committed; generate them with export_weights.py. The env var lets
# deployments / tests point at an alternate location without code changes.
DEFAULT_WEIGHTS_PATH: Path = Path(__file__).parent / "weights" / "model.weights.h5"

_MODEL: keras.Model | None = None  # lazily-loaded process-wide singleton


def build_model() -> keras.Model:
    """Reconstruct the custom CNN architecture (uncompiled).

    Three ``Conv -> BatchNorm -> MaxPool`` blocks with the filter count doubling each
    block (32 -> 64 -> 128) so the network learns progressively more abstract features,
    then a dense head. This matches the notebook cell exactly; the layer order and
    shapes must stay identical or ``load_weights`` below will fail.

    The model is left uncompiled on purpose: the notebook trained with a custom
    ``focal_loss``, but inference only needs the forward pass, so we avoid pulling
    that loss (and its ``custom_objects`` bookkeeping) into the backend.
    """
    model = keras.Sequential(
        [
            keras.layers.Input(shape=(INPUT_SIZE[1], INPUT_SIZE[0], 3)),
            keras.layers.Conv2D(32, (3, 3), activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D(2, 2),
            keras.layers.Conv2D(64, (3, 3), activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D(2, 2),
            keras.layers.Conv2D(128, (3, 3), activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D(2, 2),
            keras.layers.Flatten(),
            keras.layers.Dense(128, activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.6),  # dropout is inert at inference time
            keras.layers.Dense(1, activation="sigmoid"),
        ],
        name="medlens_cnn",
    )
    return model


def load_model(weights_path: str | os.PathLike[str] = DEFAULT_WEIGHTS_PATH) -> keras.Model:
    """Build the architecture and load trained weights from ``weights_path``."""
    weights_path = Path(weights_path)
    if not weights_path.is_file():
        raise FileNotFoundError(
            f"No trained weights at {weights_path}. Generate them once with:\n"
            f"    python backend/app/ml/export_weights.py --data-dir /path/to/chest_xray"
        )
    model = build_model()
    model.load_weights(weights_path)
    return model


def preprocess(image: Image.Image) -> np.ndarray:
    """Turn a PIL image into a model-ready batch of shape ``(1, 64, 64, 3)``.

    Reproduces Keras' ``flow_from_directory`` + ``ImageDataGenerator(rescale=1./255)``
    used for evaluation in the notebook: force 3-channel RGB, nearest-neighbour resize
    to 64x64, then scale pixels from [0, 255] to [0, 1]. No augmentation.
    """
    image = image.convert("RGB").resize(INPUT_SIZE, Image.NEAREST)
    array = np.asarray(image, dtype="float32") / 255.0
    return np.expand_dims(array, axis=0)


def _get_model() -> keras.Model:
    """Return the cached singleton, loading it (once) from the configured weights path."""
    global _MODEL
    if _MODEL is None:
        _MODEL = load_model(os.environ.get("MEDLENS_WEIGHTS_PATH", DEFAULT_WEIGHTS_PATH))
    return _MODEL


def predict(
    image: Image.Image,
    model: keras.Model | None = None,
    *,
    with_heatmap: bool = False,
) -> dict[str, object]:
    """Classify a single chest X-ray.

    Args:
        image: the X-ray as a PIL image (any mode/size — it is normalised here).
        model: an optional pre-built model. When omitted, a lazily-loaded singleton
            backed by the trained weights file is used.
        with_heatmap: also compute a Grad-CAM overlay and include it under
            ``"heatmap"`` as a base64 PNG ``data:`` URI.

    Returns:
        ``{"label": "NORMAL" | "PNEUMONIA", "probability": <float>}`` (plus
        ``"heatmap"`` when requested) where ``probability`` is always P(PNEUMONIA),
        the raw sigmoid output — not the confidence of the returned label.
    """
    model = model if model is not None else _get_model()
    batch = preprocess(image)
    prob_pneumonia = float(model.predict(batch, verbose=0)[0][0])
    result: dict[str, object] = {
        "label": CLASS_NAMES[int(prob_pneumonia > DECISION_THRESHOLD)],
        "probability": prob_pneumonia,
    }
    if with_heatmap:
        from app.ml.gradcam import overlay_data_uri  # lazy: keeps matplotlib off the hot path

        result["heatmap"] = overlay_data_uri(model, batch, image)
    return result
