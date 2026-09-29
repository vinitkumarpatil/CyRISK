# CLAUDE.md — RiskQuant Project Context

> **Entry point for any new chat.** Read this first, then `docs/FILE_INDEX.md` for "where does X live", then the area doc you need. `GEMINI.md` is byte-for-byte identical to this file — edit one, copy to the other.

## What this is
**RiskQuant** — a continuous **Cyber Risk Quantification** platform. It ingests an org's assets, vulnerabilities, and security controls and computes financial risk (Annualized Loss Expectancy in ₹) using the **FAIR** model, plus Value-at-Risk (Monte Carlo), control recommendations, a knapsack **investment optimizer**, scenario analysis, framework/compliance mapping, and PDF reports. Multi-tenant, with a seeded demo org for presentation.

## Tech stack
- **Backend** (`backend/`) — FastAPI 0.141 + SQLAlchemy 2.1 + Pydantic 2.13, SQLite (`cyberrisk.db`), numpy/pandas/scipy/scikit-learn, reportlab (PDF), uvicorn. Python 3.14, venv at `backend/.venv` (`./.venv/Scripts/python.exe`). **FROZEN** — see rules.
- **Frontend** (`frontend/`) — Vite 5.4 + React 18.3 + TypeScript 5.6 (strict) + Tailwind 3.4 + Recharts 2.12 + lucide-react + react-router-dom 6.
- **Platform** — Windows 11 / Git Bash. **Not a git repo.**

## Architecture in one paragraph
Browser SPA (`:5173`, Vite dev) calls `/api/*`, proxied to FastAPI (`:8000`). FastAPI routers (`app/routers/`) validate the bearer token, derive `org_id` server-side (`Depends(current_org)`), and delegate risk math to the engine (`app/engine/`). SQLAlchemy models (`app/models/`) persist to SQLite; every business table has an `org_id` for tenant isolation. On startup the app auto-seeds the demo org **"Meghdoot Financial Services Ltd (DEMO)"**. See `docs/ARCHITECTURE.md`.

## Run it (full detail in `docs/RUNBOOK.md`)
```bash
# backend  (:8000)
cd backend && ./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
# frontend (:5173, proxies /api → :8000)
cd frontend && npm run dev
# checks
cd frontend && npm run typecheck && npm run build
cd backend && ./.venv/Scripts/python.exe -m pytest -q
```
Demo logins: `exec/exec123` (read-only), `ciso/ciso123`, `analyst/analyst123`. Token in `localStorage.sih_token`; theme in `localStorage.sih_theme` (default `night`).

## HARD RULES (full list in `docs/CONVENTIONS.md`)
1. **Backend is FROZEN** — never change `backend/` APIs, calculations, DB, auth, or seed data. If a change seems to need the backend, STOP and report.
2. **No registration UI** — deleted on purpose; only the 3 demo accounts log in.
3. **All money is ₹** — format only via `inr()` in `src/lib/format.ts`.
4. **No SIH problem-statement IDs** in visible UI.
5. **Two themes (Day/Night)** — semantic tokens only, never raw colors; every change works in both.
6. **Numbers come from the backend** — never fake risk/financial values client-side.

## Compact repo map
```
SIH26105/
├─ backend/                 FastAPI service (FROZEN)
│  ├─ app/
│  │  ├─ main.py            app factory, router mounts, lifespan/auto-seed
│  │  ├─ config.py database.py deps.py auth.py schemas.py
│  │  ├─ engine/            risk math: financial, risk_engine, optimizer,
│  │  │                     scenarios, recommend, controls, criticality,
│  │  │                     snapshots, nlq, ml_model, reports, frameworks_data,
│  │  │                     constants, state
│  │  ├─ models/            core, decisions, frameworks, risk, security, users
│  │  ├─ routers/           assets, assistant, assumptions, auth, controls,
│  │  │                     dashboard, demo, frameworks, imports, investments,
│  │  │                     model_info, optimizer, recommendations, reports,
│  │  │                     risk, scenarios, telemetry, vulnerabilities
│  │  └─ seed/              catalog, enterprise, frameworks_catalog,
│  │                        investments, loader, vulns
│  ├─ tests/                conftest, test_api, test_engine, test_tenant_isolation
│  ├─ requirements.txt      cyberrisk.db (SQLite, auto-created)
│  └─ .venv/                Python 3.14 virtualenv
├─ frontend/                Vite + React SPA
│  ├─ public/riskquant-logo.webp   the brand logo (referenced as /riskquant-logo.webp)
│  ├─ index.html            title "RiskQuant", favicon = logo
│  └─ src/
│     ├─ App.tsx            route table (path → page)
│     ├─ main.tsx           providers: ThemeProvider → BrowserRouter → AuthProvider
│     ├─ index.css          theme tokens + component classes (.card/.btn-*/.input)
│     ├─ api/               client.ts (get/post/del + bearer), types.ts
│     ├─ auth/AuthContext.tsx   login/logout/me, demo users
│     ├─ components/        Layout (shell/sidebar/topbar), ui (primitives),
│     │                     charts, DataTable, Modal
│     ├─ lib/               format.ts (inr, pct, bandChip…), useApi.ts
│     ├─ pages/             one .tsx per route (Dashboard, RiskAnalysis, Assets,
│     │                     Vulnerabilities, Controls, Recommendations, Scenarios,
│     │                     Optimizer, Frameworks, Assumptions, Assistant,
│     │                     ModelCard, DataSources/Telemetry, Reports, Login)
│     └─ theme/ThemeContext.tsx   Day/Night, chart palette
├─ docs/                    context docs (this folder)
├─ .claude/skills/          web-dev, ui-design, context-manager, productivity
└─ _recovery_snapshot_20260929_222809/   pre-redesign backup — DO NOT DELETE
```

## The docs (read the one that fits the task)
- **`docs/FILE_INDEX.md`** — exhaustive file-by-file "where do I change X" map. Start here to locate code.
- **`docs/ARCHITECTURE.md`** — system design, data flow, the risk engine & formulas.
- **`docs/FRONTEND.md`** — pages, components, routing, theming, "where does this UI live".
- **`docs/BACKEND.md`** — routers→endpoints, engine modules, models, seed (reference only; frozen).
- **`docs/CONVENTIONS.md`** — coding rules + the hard constraints above (expanded).
- **`docs/RUNBOOK.md`** — install, run, test, build, common tasks, troubleshooting.

## Skills (`.claude/skills/`)
- **web-dev** — frontend dev workflow + mandatory verify-in-browser steps.
- **ui-design** — the Day/Night design system and review checklist.
- **context-manager** — bootstrap a new session; keep these docs true.
- **productivity** — safe-change task loop and how to scope/sequence work.

## Persistent memory
Cross-session facts live at
`C:\Users\vtkr5\.claude\projects\C--Users-vtkr5-Desktop-SIH26105\memory\` (index: `MEMORY.md`).
When a constraint or structural decision changes, update `docs/CONVENTIONS.md` **and** the memory file.
