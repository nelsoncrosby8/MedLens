"""Password hashing (passlib/bcrypt) and JWT creation/decoding (python-jose)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for ``password``."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plaintext ``password`` against a stored bcrypt hash."""
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Encode a signed JWT whose ``sub`` claim is ``subject`` (here: the user's email)."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the ``sub`` claim from a valid token, or ``None`` if it is invalid/expired."""
    try:
        payload = jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
