#!/usr/bin/env sh
# Applies pending Alembic migrations, then runs the given command (uvicorn by default).
# compose already gates startup on the db healthcheck, so the database is reachable here.
set -e

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

echo "[entrypoint] exec: $*"
exec "$@"
