# MedLens

A full-stack web app where a user uploads a chest X-ray and receives an AI-assisted
pneumonia triage result (probability + Grad-CAM heatmap), with accounts and case history.
This is a portfolio project — code quality, tests, and real deployability are the focus.

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

Next: Docker Compose for the full stack, CI, deployment, README polish.

## Repository layout

```
backend/
  app/
    api/        FastAPI routers (one per resource) — not built yet
    core/       config / settings
    ml/         model architecture + inference (model.py) and a manual
                training/export script (export_weights.py)
    models/     SQLAlchemy models — not built yet
    schemas/    Pydantic schemas — not built yet
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

## Data

Only public, de-identified datasets are used (Kaggle Chest X-Ray Pneumonia). No patient data
or PHI is stored in this repository.
