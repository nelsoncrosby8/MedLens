"""One-off trainer that produces the weights file ``model.py`` expects.

This is the ONLY training code in the backend. It is meant to be run **manually** from
the command line, never imported by the application. It reproduces the custom-CNN
training run from ``notebooks/pneumonia_classifier.ipynb`` and writes weights-only to
``backend/app/ml/weights/model.weights.h5``.

Usage (run from the ``backend/`` directory so ``app`` is importable):
    cd backend && python -m app.ml.export_weights --data-dir /path/to/chest_xray

``--data-dir`` must contain a ``train/`` folder with ``NORMAL/`` and ``PNEUMONIA/``
subfolders (the Kaggle "Chest X-Ray Images (Pneumonia)" layout). Training runs on CPU
in roughly 30-45 minutes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from app.ml.model import DEFAULT_WEIGHTS_PATH, INPUT_SIZE, build_model

SEED = 42
BATCH_SIZE = 32


def focal_loss(gamma: float = 2.0, alpha: float = 0.25):
    """Focal loss, copied verbatim from the notebook.

    Handles the NORMAL/PNEUMONIA class imbalance: ``alpha`` re-weights the classes and
    ``gamma`` focuses training on hard examples. Only needed while training.
    """

    def loss(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        bce = -y_true * tf.math.log(y_pred) - (1 - y_true) * tf.math.log(1 - y_pred)
        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
        focal_weight = alpha_t * tf.pow(1 - p_t, gamma)
        return tf.reduce_mean(focal_weight * bce)

    return loss


def build_generators(data_dir: Path):
    """Recreate the notebook's train/val generators (80/20 split of ``train/``)."""
    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
        rotation_range=15,
        zoom_range=0.1,
        horizontal_flip=True,
    )
    common = dict(
        directory=str(data_dir / "train"),
        target_size=INPUT_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",
        seed=SEED,
    )
    train_data = train_gen.flow_from_directory(subset="training", **common)
    val_data = train_gen.flow_from_directory(subset="validation", **common)
    return train_data, val_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / "Downloads" / "chest_xray",
        help="Kaggle chest_xray dataset root (must contain train/NORMAL and train/PNEUMONIA).",
    )
    parser.add_argument("--epochs", type=int, default=30, help="Max training epochs (early stopping applies).")
    parser.add_argument("--out", type=Path, default=DEFAULT_WEIGHTS_PATH, help="Where to write the weights file.")
    args = parser.parse_args()

    if not (args.data_dir / "train").is_dir():
        parser.error(f"{args.data_dir / 'train'} not found — pass --data-dir pointing at the dataset root.")

    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    train_data, val_data = build_generators(args.data_dir)

    # Balanced class weights, exactly as in the notebook.
    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(train_data.classes),
        y=train_data.classes,
    )
    class_weight_dict = dict(enumerate(class_weights))
    print(f"Class weights: {class_weight_dict}")

    model = build_model()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss=focal_loss(gamma=2.0, alpha=0.25),
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=7, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1
        ),
    ]

    model.fit(
        train_data,
        epochs=args.epochs,
        validation_data=val_data,
        callbacks=callbacks,
        class_weight=class_weight_dict,
        verbose=1,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    model.save_weights(args.out)
    print(f"\nSaved weights to {args.out}")
    print("Now run:  cd backend && pytest -q")


if __name__ == "__main__":
    main()
