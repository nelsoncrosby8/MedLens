"""Pydantic schemas for the /predict endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    """Classifier output for a single chest X-ray.

    Mirrors the dict returned by ``app.ml.model.predict``.
    """

    label: str = Field(
        ...,
        description='Predicted class: "NORMAL" or "PNEUMONIA".',
        examples=["PNEUMONIA"],
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Model-estimated probability of pneumonia (the raw sigmoid output, "
            "i.e. P(PNEUMONIA)); not the confidence of the returned label."
        ),
        examples=[0.9137],
    )
