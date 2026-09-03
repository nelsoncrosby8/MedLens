# MedLens frontend

React (Vite + TypeScript) client for the MedLens API. See the repo root `README.md` for the
project overview and the **Frontend** section there for setup.

```bash
npm install
npm run dev     # http://localhost:5173  (needs the API on http://localhost:8000)
npm run build
npm run lint
npm run test    # Vitest
```

Configure the API base URL with `VITE_API_URL` (see `.env.example`).

Layout (`src/`, by feature): `lib/` API client + types · `auth/` context + login/signup ·
`upload/` X-ray upload + results view · `history/` history dashboard · `components/` shared UI.
