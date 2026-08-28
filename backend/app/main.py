"""MedLens FastAPI application.

Milestone 2: serves ``/health`` and ``/predict``. No database, auth, or frontend yet
— those are later milestones.

**Not for clinical use** — educational/portfolio project only.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import predict as predict_api
from app.ml.model import load_model

DISCLAIMER = (
    "For educational/portfolio purposes only. Not a certified medical device and "
    "not intended for clinical diagnosis."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the CNN + trained weights exactly once, at startup.

    Storing the model on ``app.state`` means no request pays the weight-loading
    cost and every request shares a single in-memory model instance.
    """
    app.state.model = load_model()
    try:
        yield
    finally:
        app.state.model = None


app = FastAPI(
    title="MedLens API",
    version="0.2.0",
    summary="AI-assisted pneumonia triage from chest X-rays.",
    description=DISCLAIMER,
    lifespan=lifespan,
)

app.include_router(predict_api.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe. Returns ``{"status": "ok"}`` while the app is running."""
    return {"status": "ok"}
