# RUNBOOK — Install, Run, Test, Build

> Windows + Git Bash. Repo root: `C:\Users\vtkr5\Desktop\SIH26105`. Not a git repo.

## Prerequisites
- **Python 3.14** with the backend virtualenv at `backend/.venv` (cp314 wheels). Use `backend/.venv/Scripts/python.exe`.
- **Node.js** (for Vite 5). Frontend deps in `frontend/`.

## Backend (FastAPI, port 8000)
Install (first time):
```bash
cd backend && ./.venv/Scripts/python.exe -m pip install -r requirements.txt
```
Run the API server:
```bash
cd backend && ./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```
- SQLite DB file: `backend/cyberrisk.db` (auto-created).
- On first startup the app auto-seeds the demo org **"Meghdoot Financial Services Ltd (DEMO)"** via the FastAPI lifespan (see `app/main.py` → `app/seed/loader.py`).
- OpenAPI/Swagger: http://127.0.0.1:8000/docs
- ⚠️ **After adding/removing a route, RESTART uvicorn.** A stale `--reload` process has served an outdated OpenAPI (caused a phantom "404 Not Found" before). If a new route 404s, restart the server first.

## Frontend (Vite + React, port 5173)
Install (first time):
```bash
cd frontend && npm install
```
Dev server (proxies `/api` → `http://127.0.0.1:8000`):
```bash
cd frontend && npm run dev
```
- App: http://localhost:5173  (backend must be running on :8000 for data).
- In the Claude desktop app, the preview uses the `frontend-dev` config in `.claude/launch.json` (host 127.0.0.1, port 5173). Prefer the `preview_*` tools over manual server starts.

## Type-check / Build
```bash
cd frontend && npm run typecheck   # tsc --noEmit — must be clean (exit 0)
cd frontend && npm run build        # vite build — must succeed
```
- A single **">500 kB chunk size" warning is expected and pre-existing** — not an error.

## Tests (backend)
```bash
cd backend && ./.venv/Scripts/python.exe -m pytest -q
```
- Suites: `tests/test_api.py`, `tests/test_engine.py`, `tests/test_tenant_isolation.py` (fixtures in `tests/conftest.py`).

## Demo accounts (only these 3 exist in the UI)
| Role | Username | Password | Can mutate? |
|---|---|---|---|
| Executive | `exec` | `exec123` | read-only |
| CISO | `ciso` | `ciso123` | yes |
| Analyst | `analyst` | `analyst123` | yes |
Auth token is stored in `localStorage` under `sih_token`. Theme under `sih_theme` (`day`/`night`, default night).

## Common tasks
- **Simulate telemetry** (adds a snapshot, re-scores risk): topbar "Simulate Telemetry" button (ciso/analyst) → `POST /api/demo/simulate-telemetry` → fires `risk-refresh` event so pages reload.
- **Reset demo data:** `POST /api/demo/load` (demo org only).
- **Download a report PDF:** Reports page → `GET /api/reports/{id}/download`.

## Troubleshooting
- **Port 5173 in use:** find and kill the stale node process (`taskkill //PID <pid> //F`) then restart the dev server.
- **New backend route 404s:** restart uvicorn (see warning above).
- **Blank/₹0 dashboard for a new org:** expected — ALE needs active vulnerabilities; a new org with assets but no vulns shows ₹0 (FAIR model). The seeded demo org has full data.
- **Recharts `defaultProps` console warnings:** harmless library deprecation warnings; ignore.

## Recovery
- A recovery snapshot of the pre-redesign state exists at `_recovery_snapshot_20260929_222809/`. Do not delete it.
