"""Importing this package registers every model on ``Base.metadata`` (for Alembic autogenerate)."""

from app.models.prediction import Prediction  # noqa: F401
from app.models.user import User  # noqa: F401
