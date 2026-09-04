#!/usr/bin/env sh
# Applies pending Alembic migrations, then runs the given command (uvicorn by default).
# compose already gates startup on the db healthcheck, so the database is reachable here.
set -e

WEIGHTS_PATH="${MEDLENS_WEIGHTS_PATH:-/app/app/ml/weights/model.weights.h5}"

# Local dev bind-mounts the weights from the host. Deploys (e.g. Render) don't have
# them in the build context (gitignored), so fetch from a GitHub Release asset instead.
# MODEL_WEIGHTS_ASSET_URL is the release asset's API URL (…/releases/assets/<id>), which
# works for a private repo when GH_TOKEN is a token with read access to it.
if [ ! -f "$WEIGHTS_PATH" ] && [ -n "$MODEL_WEIGHTS_ASSET_URL" ]; then
  echo "[entrypoint] weights not found at $WEIGHTS_PATH; downloading…"
  mkdir -p "$(dirname "$WEIGHTS_PATH")"
  # NB: don't use `set --` here — it would overwrite the script's own "$@" (this
  # container's CMD), which `exec "$@"` below still needs.
  if [ -n "$GH_TOKEN" ]; then
    curl -fSL -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/octet-stream" \
      "$MODEL_WEIGHTS_ASSET_URL" -o "$WEIGHTS_PATH"
  else
    curl -fSL -H "Accept: application/octet-stream" \
      "$MODEL_WEIGHTS_ASSET_URL" -o "$WEIGHTS_PATH"
  fi
  echo "[entrypoint] downloaded $(wc -c <"$WEIGHTS_PATH") bytes"
fi

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

echo "[entrypoint] exec: $*"
exec "$@"
