"""``/history`` — the authenticated caller's past predictions."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.predict import PredictionRead

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[PredictionRead])
def list_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200, description="Max rows to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip (for paging).")] = 0,
) -> list[Prediction]:
    """Return the caller's predictions, newest first. Requires a bearer token."""
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
