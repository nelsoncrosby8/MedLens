# MedLens

[![CI](https://github.com/nelsoncrosby8/MedLens/actions/workflows/ci.yml/badge.svg)](https://github.com/nelsoncrosby8/MedLens/actions/workflows/ci.yml)

A full-stack web app where a user uploads a chest X-ray and receives an AI-assisted
pneumonia triage result (probability + Grad-CAM heatmap), with accounts and case history.
This is a portfolio project — code quality, tests, and real deployability are the focus.

**Live API:** https://medlens-backend-lrwv.onrender.com/docs (free tier — the first request
after idle can be slow; see [Deployment](#deployment)). The frontend isn't deployed yet, so
drive it via Swagger or point a local `npm run dev` at it.

> **Disclaimer:** For educational/portfolio purposes only. Not a certified medical device
> and not intended for clinical diagnosis.

## Status

Built in milestones (see `CLAUDEmedlens.md`). Done so far:

- **1–2** ML inference module + FastAPI service (`/health`, `/predict`).
- **3** PostgreSQL models, Alembic migrations, JWT auth (`/auth/signup|login|me`).
- **4** Per-user prediction persistence + `GET /history`; `/predict` now requires auth; CORS.
- **5** Grad-CAM heatmap in the `/predict` response.
- **6** React (Vite + TS) frontend: login/signup, X-ray upload, results view with the
  heatmap, and a history dashboard — all wired to the API.
- **7** `docker compose up` full local stack (db + backend + frontend, hot reload).
- **8** GitHub Actions CI — ruff lint/format + pytest (backend), oxlint + build + Vitest
  (frontend) — on every PR and on `main`.
- **9** Backend + database deployed live to Render (free tier); deploy-on-merge to `main`.

Next: README polish.

## Repository layout

```
backend/
  app/
    api/        FastAPI routers: auth, predict, history
    core/       config / settings, DB session, security (hashing + JWT)
    ml/         model architecture + inference (model.py), Grad-CAM (gradcam.py),
                and a manual training/export script (export_weights.py)
    models/     SQLAlchemy models (User, Prediction)
    schemas/    Pydantic schemas
  alembic/      migrations
  tests/        pytest suite (+ sample chest X-ray fixtures under tests/data/)
frontend/       React (Vite + TypeScript) app, organized by feature
  src/
    lib/        typed fetch API client + shared types
    auth/       auth context, login / signup pages
    upload/     X-ray upload flow + results view (label, probability, heatmap toggle)
    history/    prediction history dashboard
    components/ shared UI (nav, disclaimer footer, spinner, …)
notebooks/      the original model-development notebook
```

## ML model

The classifier is the custom CNN from the notebook: a 3-block Conv net on 64x64 RGB inputs,
sigmoid output, `NORMAL = 0` / `PNEUMONIA = 1`, decision threshold 0.5. `backend/app/ml/model.py`
rebuilds that architecture and loads trained weights; it does **not** train.

### Producing the weights file

No trained weights are committed. Generate `backend/app/ml/weights/model.weights.h5` once
(run from `backend/` so the `app` package is importable):

```bash
cd backend && python -m app.ml.export_weights --data-dir /path/to/chest_xray
```

`--data-dir` must point at the Kaggle "Chest X-Ray Images (Pneumonia)" dataset (a `train/`
and `test/` folder, each with `NORMAL/` and `PNEUMONIA/` subfolders). Training runs on CPU
and takes roughly 30–45 minutes.

## Development

Requires Python 3.11 (the pinned TensorFlow build does not support 3.12+).

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend && pytest -q
```

The weight-dependent test is skipped until you have run `export_weights.py`.

### Frontend

Needs Node 20+ and the backend running on `http://localhost:8000`.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Point it at a different API with `VITE_API_URL` (see `frontend/.env.example`). Other scripts:
`npm run build`, `npm run lint`, `npm run test` (Vitest). The backend's `CORS_ORIGINS`
already allows `http://localhost:5173`.

### Docker (full stack)

Brings up **db + backend + frontend** with one command (needs Docker, or Colima):

```bash
docker compose up --build
```

- frontend → `http://localhost:5173`  •  backend → `http://localhost:8000`  •  db → `localhost:5433`
- Both app services run their dev servers with the source bind-mounted (hot reload).
- The backend container runs `alembic upgrade head` on startup.
- Postgres is published on **5433** so it doesn't collide with a local Postgres on 5432.
- The backend still needs `backend/app/ml/weights/model.weights.h5` on the host (see above) —
  it's read through the bind mount, not baked into the image.

`docker compose down` stops it; add `-v` to also drop the database volume.

TensorFlow needs headroom — if you're on Colima, give the VM some RAM:
`colima start --memory 4`.

## Deployment

**Live:** https://medlens-backend-lrwv.onrender.com — verified end-to-end (signup, login,
`/predict` with real inference + Grad-CAM in ~3s, `/history`, and the 401/400 error paths).

The **backend + database** are deployed to [Render](https://render.com) on the free tier via
the `render.yaml` Blueprint at the repo root (the frontend isn't deployed yet). Render
auto-deploys on every push to `main`.

**Free-tier tradeoffs, going in with eyes open:**
- The web service spins down after 15 min idle; the next request pays a cold start
  (Render's own ~1 min, *plus* TensorFlow import/model load on top).
- Free instances get 512 MB RAM / 0.1 vCPU — tight for TensorFlow. It may be slow; it could
  even OOM under load. If that happens, the fix is a paid instance type, not more code.
- The free Postgres database **expires 30 days after creation** (Render deletes it, with a
  14-day warned grace period first). This is a demo deployment, not a durable one — treat
  any data in it as disposable, and expect to recreate the Blueprint periodically.

**One-time setup:**
1. In Render: **New → Blueprint**, point it at this repo. Render parses `render.yaml` and
   shows an editable preview of the `medlens-backend` web service and `medlens-db` database
   — confirm both on the **Free** plan and create them.
2. The trained weights aren't in git (see above), so the container fetches them from a
   [GitHub Release asset](https://github.com/nelsoncrosby8/MedLens/releases/tag/weights-v1)
   at startup — `docker-entrypoint.sh` does this before running migrations. Since the repo is
   private, that download needs a token. In the Render dashboard, set on `medlens-backend`:
   - `MODEL_WEIGHTS_ASSET_URL` = the release asset's **API** URL (not the browser download
     link): `https://api.github.com/repos/nelsoncrosby8/MedLens/releases/assets/<id>`
     (`gh api repos/nelsoncrosby8/MedLens/releases/tags/weights-v1 --jq '.assets[0].url'`).
   - `GH_TOKEN` = a GitHub token with read access to this repo (Settings → Developer settings →
     Fine-grained tokens → this repo only → **Contents: Read-only**). Treat it as a secret.
3. Everything else (`DATABASE_URL`, `SECRET_KEY`, CORS, etc.) is already wired in
   `render.yaml` — `DATABASE_URL` comes from the Blueprint's own database, `SECRET_KEY` is
   auto-generated by Render.
4. First deploy: Render builds the image, the entrypoint downloads the weights and runs
   `alembic upgrade head`, then uvicorn starts. Check `<your-service>.onrender.com/health`
   and `/docs`.

To redeploy after that, just merge to `main` — no extra steps.

## Data

Only public, de-identified datasets are used (Kaggle Chest X-Ray Pneumonia). No patient data
or PHI is stored in this repository.
