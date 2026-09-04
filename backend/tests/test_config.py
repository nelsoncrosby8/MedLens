"""Settings behavior that matters for deployment: DATABASE_URL driver normalization."""

from app.core.config import Settings


def test_bare_postgres_scheme_gets_psycopg2_driver():
    s = Settings(DATABASE_URL="postgres://user:pw@host:5432/db")
    assert s.DATABASE_URL == "postgresql+psycopg2://user:pw@host:5432/db"


def test_bare_postgresql_scheme_gets_psycopg2_driver():
    s = Settings(DATABASE_URL="postgresql://user:pw@host:5432/db")
    assert s.DATABASE_URL == "postgresql+psycopg2://user:pw@host:5432/db"


def test_explicit_driver_is_left_alone():
    s = Settings(DATABASE_URL="postgresql+psycopg2://user:pw@host:5432/db")
    assert s.DATABASE_URL == "postgresql+psycopg2://user:pw@host:5432/db"


def test_sqlite_url_is_left_alone():
    s = Settings(DATABASE_URL="sqlite:///./dev.db")
    assert s.DATABASE_URL == "sqlite:///./dev.db"
