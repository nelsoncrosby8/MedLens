"""Application settings, loaded from environment variables / a local ``.env`` file.

Every value has a development default so the app and tests import cleanly without a
``.env``. Production **must** override at least ``SECRET_KEY`` and ``DATABASE_URL``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # SQLAlchemy URL. Defaults to the docker-compose / local Postgres role.
    DATABASE_URL: str = "postgresql+psycopg2://medlens:medlens@localhost:5432/medlens"

    # JWT signing. The default is insecure and for local dev only — set a long random
    # value in the environment for anything shared or deployed.
    SECRET_KEY: str = "dev-only-insecure-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (read once per process)."""
    return Settings()
