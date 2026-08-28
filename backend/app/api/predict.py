"""``/predict`` — run the pneumonia classifier on an uploaded chest X-ray."""

from __future__ import annotations

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.ml.model import predict as run_inference
from app.schemas.predict import PredictResponse

router = APIRouter(tags=["prediction"])

# Uploads above this are rejected before we buffer the whole body / hand it to PIL.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
_READ_CHUNK = 64 * 1024


def get_model(request: Request):
    """Return the model loaded once at startup (see ``app.main.lifespan``).

    Exposed as a dependency so tests can override it via ``app.dependency_overrides``.
    """
    model = getattr(request.app.state, "model", None)
    if model is None:  # pragma: no cover - lifespan always sets this in practice
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded.",
        )
    return model


async def _read_within_limit(upload: UploadFile) -> bytes:
    """Read the full upload, aborting with 413 as soon as it exceeds the size cap."""
    buffer = io.BytesIO()
    total = 0
    while chunk := await upload.read(_READ_CHUNK):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File too large; limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )
        buffer.write(chunk)
    return buffer.getvalue()


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: Annotated[UploadFile, File(description="Chest X-ray image (JPEG or PNG, max 5 MB).")],
    model: Annotated[object, Depends(get_model)],
) -> PredictResponse:
    """Classify an uploaded chest X-ray as **NORMAL** or **PNEUMONIA**.

    Send one image as ``multipart/form-data`` under the field name ``file``. The
    response contains the predicted label and the model's estimated probability of
    pneumonia (`P(PNEUMONIA)`, the raw sigmoid output).

    Errors:
    - **400** — the upload is missing, empty, or not a decodable image.
    - **413** — the upload exceeds the 5 MB limit.

    **Not for clinical use** — educational/portfolio project only.
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected an image upload, got content type '{file.content_type}'.",
        )

    contents = await _read_within_limit(file)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty upload.",
        )

    # Don't trust the declared content type — actually decode the bytes.
    try:
        Image.open(io.BytesIO(contents)).verify()  # structural check; consumes the object
        image = Image.open(io.BytesIO(contents))  # reopen for real use
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a readable image.",
        ) from exc

    result = run_inference(image, model=model)
    return PredictResponse(**result)
