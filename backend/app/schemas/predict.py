"""Pydantic schemas for the /predict and /history endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_PROBABILITY_DESCRIPTION = (
    "Model-estimated probability of pneumonia (the raw sigmoid output, i.e. "
    "P(PNEUMONIA)); not the confidence of the returned label."
)


class PredictResponse(BaseModel):
    """Result of classifying one chest X-ray, as persisted to the caller's history."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID of the stored prediction (see GET /history).")
    label: str = Field(
        ..., description='Predicted class: "NORMAL" or "PNEUMONIA".', examples=["PNEUMONIA"]
    )
    probability: float = Field(
        ..., ge=0.0, le=1.0, description=_PROBABILITY_DESCRIPTION, examples=[0.9137]
    )
    created_at: datetime = Field(..., description="When the prediction was made (UTC).")


class PredictionRead(BaseModel):
    """One row from the caller's prediction history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    probability: float = Field(..., ge=0.0, le=1.0, description=_PROBABILITY_DESCRIPTION)
    filename: str | None = Field(None, description="Original upload filename, if the client sent one.")
    created_at: datetime
