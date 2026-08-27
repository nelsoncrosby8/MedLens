# CLAUDE.md — Project context for Claude Code

## Project
MedLens: a full-stack web app where a user uploads a chest X-ray and receives an AI-assisted
pneumonia triage result (probability + Grad-CAM heatmap), with accounts and case history.
This is a portfolio/resume project — code quality, tests, and real deployability matter more
than model accuracy.

## Non-negotiable guardrails
- This is NOT a diagnostic medical device. Every user-facing screen and the README must carry
  a visible disclaimer: "For educational/portfolio purposes only. Not a certified medical
  device and not intended for clinical diagnosis."
- Only use public, de-identified datasets (e.g., Kaggle Chest X-Ray Pneumonia dataset). Never
  add real patient data or PHI to this repo.
- Never commit secrets. All credentials/config via `.env`, loaded through `backend/app/core/config.py`.

## Tech stack (do not deviate without discussion)
- Backend: Python 3.11+, FastAPI, SQLAlchemy + Alembic migrations, PostgreSQL
- ML: PyTorch (or TensorFlow — match whatever the existing trained model uses), Grad-CAM via
  `pytorch-grad-cam` (or `tf-explain`)
- Auth: JWT-based, `passlib` for hashing, `python-jose` for tokens
- Frontend: React (Vite), plain fetch/axios to the API, Tailwind for styling
- Containerization: Docker + docker-compose (services: `backend`, `frontend`, `db`)
- Tests: `pytest` + `httpx.TestClient` for backend; aim for meaningful coverage over 100% vanity
  coverage
- CI: GitHub Actions — lint (`ruff`/`black`) + test on every PR

## Repository conventions
- Backend code lives under `backend/app/`, organized by concern: `api/`, `core/`, `models/`,
  `ml/`, `schemas/`. One router per resource (`auth`, `upload`, `predict`, `history`).
- Every new endpoint needs: a Pydantic schema, a test in `backend/tests/`, and a docstring
  visible in the auto-generated Swagger docs.
- Frontend code lives under `frontend/src/`, organized by feature (`upload/`, `history/`,
  `auth/`).
- Write small, reviewable commits. Prefer several small PRs over one giant one.

## How to work with me on this
- Build in the milestone order below. Don't jump ahead to the frontend before the backend
  `/predict` endpoint has a passing test.
- Always add or update tests in the same change as the feature, not as a follow-up.
- When implementing ML inference, treat the trained model file as a black box loaded from
  `backend/app/ml/model.py` — do not attempt to retrain or tune it unless explicitly asked.
- Explain non-obvious code choices in comments so the human reviewer (me) can defend every
  line of this code in a job interview.

## Milestone order (see MedLens_Project_Plan.md for full detail)
1. Backend skeleton + health-check endpoint + pytest wired up
2. `/predict` endpoint (model inference, no DB yet)
3. PostgreSQL models + Alembic migrations + auth (signup/login)
4. Persist predictions per user; `/history` endpoint
5. Grad-CAM heatmap added to `/predict` response
6. React frontend: upload flow, results view, history dashboard
7. Docker Compose for full local stack
8. GitHub Actions CI (lint + test on PR)
9. Deployment (Render/Railway/Fly.io) + deploy-on-merge
10. README polish: architecture diagram, screenshots/GIF, disclaimer, live URL
