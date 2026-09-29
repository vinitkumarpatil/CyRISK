# FILE_INDEX.md — Exhaustive "Where Do I Change X?" Map

> Every source file, its purpose, and what to open for a given change. Paths relative to repo root `SIH26105/`.
> **Backend is FROZEN** (reference only). Frontend is where edits happen.

## Quick "I want to change X" table
| I want to change… | Open this |
|---|---|
| A page's content/layout | `frontend/src/pages/<Page>.tsx` |
| The sidebar nav / topbar / logo | `frontend/src/components/Layout.tsx` |
| A shared widget (stat card, badge, button-ish, empty/loading state) | `frontend/src/components/ui.tsx` |
| A chart's look/behavior | `frontend/src/components/charts.tsx` |
| A sortable table | `frontend/src/components/DataTable.tsx` |
| A modal/dialog | `frontend/src/components/Modal.tsx` |
| How money/percent/dates render | `frontend/src/lib/format.ts` |
| Theme colors / tokens / component classes | `frontend/src/index.css` + `frontend/tailwind.config.js` |
| Day/Night behavior or chart palette | `frontend/src/theme/ThemeContext.tsx` |
| Routes (add/rename a page) | `frontend/src/App.tsx` (+ `Layout.tsx` NAV if in sidebar) |
| Data fetching hook | `frontend/src/lib/useApi.ts` |
| API calls / token / base URL | `frontend/src/api/client.ts` |
| Response TypeScript types | `frontend/src/api/types.ts` |
| Login / auth state | `frontend/src/pages/Login.tsx` + `frontend/src/auth/AuthContext.tsx` |
| Page title / favicon | `frontend/index.html` |
| A risk formula (reference only, do not edit) | `backend/app/engine/financial.py`, `risk_engine.py`, `optimizer.py`, `scenarios.py` |
| An API endpoint (reference only, do not edit) | `backend/app/routers/<name>.py` |

---

## Frontend — `frontend/`

### Config & entry
- `index.html` — HTML shell. Title "RiskQuant", favicon `/riskquant-logo.webp`.
- `package.json` — scripts: `dev`, `build` (vite build), `preview` (:4173), `typecheck` (tsc --noEmit). name "cyberrisk-frontend".
- `vite.config.ts` — dev :5173, proxy `/api` → `http://127.0.0.1:8000`, preview :4173.
- `tailwind.config.js` — maps semantic token names → `rgb(var(--token)/<alpha>)`.
- `tsconfig*.json` — TS strict config.
- `public/riskquant-logo.webp` — the brand logo (served at `/riskquant-logo.webp`).

### `frontend/src/` root
- `main.tsx` — mount + provider nesting (ThemeProvider → BrowserRouter → AuthProvider → App).
- `App.tsx` — route table + `RequireAuth` guard. **Add/rename a route here.**
- `index.css` — Tailwind layers, theme token variables (`:root` night, `.theme-day` day), component classes (`.card`, `.card-pad`, `.btn-primary`, `.btn-ghost`, `.input`, `.chip`, `.stat-label`, `.link-muted`).
- `vite-env.d.ts` — ambient types (`ImportMetaEnv.VITE_API_BASE`).

### `frontend/src/api/`
- `client.ts` — `api.{get,post,put,del,upload,download}`, bearer via `authHeaders()`, token key `sih_token`, 401 clears token, `ApiError`. Base URL from `VITE_API_BASE` (blank in dev → proxy).
- `types.ts` — all response interfaces (User, Dashboard, RiskResult, Finding, ControlOut, Framework, OptimizeResult, Recommendation, InvestmentOption, Assumption, ScenarioResult, AssistantAnswer, Contributor, TrendPoint, …). No runtime code.

### `frontend/src/auth/`
- `AuthContext.tsx` — `{user, loading, login, register, logout}`. Endpoints: `/api/auth/me`, `/api/auth/login`, `/api/auth/demo-users`. `register()`/`/api/auth/register` exist but are **unreachable from UI** (do not surface). `fetchDemoUsers()` helper.

### `frontend/src/components/`
- `Layout.tsx` — app shell. `NAV` array (single source of sidebar items, grouped Overview/Inventory/Decisions/Governance/Intelligence/Operations), topbar (Simulate Telemetry [ciso/analyst] → ThemeToggle → user chip → Logout), org header, `Brand()` logo (`:181`). Calls `/api/demo/status`, `/api/demo/simulate-telemetry`.
- `ui.tsx` — primitives: `Card`, `CardPad`, `SectionTitle`, `StatCard`, `Money`, `RiskBadge`, `Chip`, `ProgressBar`, `Loading`, `ErrorState`, `EmptyState`, `Disclaimer`, `Explain`. Re-exports `inr`, `pct`. **Edit here to change a widget everywhere.**
- `charts.tsx` — `BarCard`, `DonutCard`, `LineCard` + local `useChartTheme()` (reads `useTheme().chart`). Money formatted via `inr()`; colors from `CHART_COLORS`.
- `DataTable.tsx` — sortable table component.
- `Modal.tsx` — modal/dialog.

### `frontend/src/lib/`
- `format.ts` — `inr`, `pct`, `pctRaw`, `num`, `shortDate`, `bandChip`, `bandHex`, `statusChip`, `CHART_COLORS`, `type Band`.
- `useApi.ts` — `useApi<T>(path, {refreshOnTelemetry?})` → `{data, loading, error, reload}`; `risk-refresh` event subscription.

### `frontend/src/theme/`
- `ThemeContext.tsx` — `Theme='day'|'night'`, `ThemeProvider`, `useTheme()`. `.theme-day` class on `documentElement`, localStorage `sih_theme` (default night), chart palettes `NIGHT_CHART`/`DAY_CHART`.

### `frontend/src/pages/` (one per route)
- `Dashboard.tsx` — `/` — executive rollup. `GET /api/dashboard`.
- `RiskAnalysis.tsx` — `/risk` — SLE→ARO→ALE + VaR. `GET /api/risk`.
- `Assets.tsx` — `/assets` — inventory + per-asset detail; create/edit/delete. `GET/POST/PUT/DELETE /api/assets(/{id})`.
- `Vulnerabilities.tsx` — `/vulnerabilities` — findings (read-only). `GET /api/vulnerabilities`.
- `Controls.tsx` — `/controls` — control effectiveness. `GET /api/controls`.
- `Recommendations.tsx` — `/recommendations` — mitigations + ROSI. `GET /api/recommendations`.
- `Scenarios.tsx` — `/scenarios` (label "What-if Scenarios") — `GET /api/investments`, `POST /api/scenarios/investment`.
- `Optimizer.tsx` — `/optimizer` (label "Investment Optimizer") — `POST /api/optimizer/run`.
- `Frameworks.tsx` — `/frameworks` — ISO/NIST/CIS/RBI/SEBI mapping. `GET /api/frameworks`.
- `Assumptions.tsx` — `/assumptions` — tunable levers. `GET/PUT /api/assumptions`.
- `Assistant.tsx` — `/assistant` (label "Risk Assistant") — `GET /api/assistant/suggestions`, `POST /api/assistant/query`.
- `ModelCard.tsx` — `/model` (label "ML Model") — `GET /api/model`.
- `DataSources.tsx` — `/telemetry` (label "Data Sources") — `GET /api/telemetry`, `GET /api/risk/snapshots`, `POST /api/demo/simulate-telemetry`.
- `Reports.tsx` — `/reports` — `GET /api/reports`, `POST /api/reports/generate`, `GET /api/reports/{id}/download`.
- `Login.tsx` — `/login` — split layout, 3 demo cards, theme toggle, logo (`:57`, `:89`). No register UI.

---

## Backend — `backend/` (FROZEN — reference only)

### `backend/app/` (top level)
- `main.py` — FastAPI app, CORS, `lifespan` (init_db → first-run `seed_demo` else `_ensure_users`), mounts all routers (no prefix here — each router self-prefixes), public `GET /` + `GET /api/health`.
- `config.py` — env config: `DATABASE_URL`, `SECRET_KEY`, `TOKEN_TTL_HOURS=12`, `CORS_ORIGINS`, upload caps/exts, currency (₹).
- `database.py` — `engine`, `SessionLocal`, `Base`, `get_db()`, `init_db()`, `_migrate_lightweight()` (adds nullable `users.org_id`).
- `deps.py` — `get_current_user`, `require_roles`, **`current_org`** (org_id from user record), per-org compute cache (`_CACHE`, `invalidate`, `get_state`, `get_result`, `get_recommendations`, `get_frameworks`, `options_for`).
- `auth.py` — HMAC token (`create_token`/`decode_token`), PBKDF2 (`hash_password`/`verify_password`).
- `schemas.py` — Pydantic v2 request/response models (LoginRequest, AssetCreate/Update, ScenarioRequest, OptimizeRequest, AssumptionUpdate, ReportRequest, …).

### `backend/app/engine/` (risk math — do not edit)
- `__init__.py` — `clamp`, `saturating`, `fmt_inr`, `pct`, `round_money`, `severity_rank`.
- `constants.py` — all tunables (severity factors, exposure multipliers, VaR seed/sims, risk-score weights, baseline controls, category→control maps).
- `financial.py` — **SLE / ARO / ALE** (`impact_components`, `frequency`, `compute_finding`), `DEFAULT_ASSUMPTIONS`.
- `risk_engine.py` — orchestrator `compute()`, `monte_carlo_var`, `_risk_score`, control/threat maps, aggregations.
- `optimizer.py` — 0/1 knapsack `optimize()`, `_knapsack`, `_investment_curve`.
- `scenarios.py` — what-if `simulate()`, `apply_mutations`, `rosi_percent`, `marginal_ale_reduction`.
- `recommend.py` — ranked recommendations with priority/ROSI/rationale.
- `controls.py` — control effectiveness scoring.
- `criticality.py` — asset criticality 0–100 + tier.
- `frameworks_data.py` — framework coverage/assessment bands.
- `ml_model.py` — GradientBoosting incident model (`IncidentModel`, `get_model`, synthetic dataset, `ml_incident_model.joblib`).
- `nlq.py` — deterministic NL query router (`answer`, `parse_amount`).
- `reports.py` — report JSON payload + reportlab PDF (`build_report`, `render_pdf`, `DISCLAIMER`, `METHODOLOGY`).
- `snapshots.py` — persist result → RiskSnapshot/Finding/Contribution; `trend`, `list_snapshots`.
- `state.py` — `build_state(db, org_id)` (DB → dict), `clone_state`.

### `backend/app/models/` (SQLAlchemy tables; all business tables carry `org_id`)
- `core.py` — `organizations` (the tenant), `business_units`, `business_services`, `assets`, `asset_dependencies`.
- `security.py` — `vulnerabilities`, `threats`, `incidents`, `controls`, `control_assessments`, `telemetry_sources`.
- `risk.py` — `financial_assumptions`, `risk_snapshots`, `risk_findings`, `risk_contributions`.
- `decisions.py` — `mitigation_actions`, `investment_options`, `scenarios`, `recommendations`, `reports`.
- `frameworks.py` — `frameworks` (global), `framework_controls` (global), `framework_mappings` (org-scoped).
- `users.py` — `users` (org_id nullable; role executive/ciso/analyst).
- `__init__.py` — re-exports all model classes (registers them on `Base`).

### `backend/app/routers/` (self-prefixed; see `docs/BACKEND.md` for full endpoint list)
`auth.py` (`/api/auth`), `demo.py` (`/api/demo`), `dashboard.py` (`/api/dashboard`), `risk.py` (`/api/risk`), `assets.py` (`/api/assets`), `vulnerabilities.py` (`/api/vulnerabilities`), `controls.py` (`/api/controls`), `telemetry.py` (`/api/telemetry`), `scenarios.py` (`/api/scenarios`), `investments.py` (`/api/investments`), `optimizer.py` (`/api/optimizer`), `frameworks.py` (`/api/frameworks`), `recommendations.py` (`/api/recommendations`), `assistant.py` (`/api/assistant`), `model_info.py` (`/api/model`), `assumptions.py` (`/api/assumptions`), `reports.py` (`/api/reports`), `imports.py` (`/api/imports`), `__init__.py` (`ALL_ROUTERS`).

### `backend/app/seed/`
- `loader.py` — `seed_demo`, `reset_demo`, `_ensure_users`, `DEMO_USERS` (exec/ciso/analyst).
- `enterprise.py` — the demo org: `ORG`, `BUSINESS_UNITS` (6), `SERVICES` (9), `ASSETS` (22), `DEPENDENCIES` (23).
- `catalog.py` — `CONTROLS` (10), `THREATS` (7), `TELEMETRY`, `ASSUMPTIONS`.
- `frameworks_catalog.py` — `FRAMEWORKS` (5: iso27001, nist_csf, CIS, RBI, SEBI) + control rows.
- `investments.py` — `INVESTMENT_OPTIONS` (14).
- `vulns.py` — `VULNERABILITIES` (~45, real CVE ids), `INCIDENTS` (7).
- `__init__.py` — re-exports `seed_demo`, `reset_demo`, `DEMO_USERS`.

### `backend/tests/`
- `conftest.py` — temp-DB redirect, `client` fixture (lifespan seed), role-header fixtures.
- `test_api.py` — integration (auth, endpoints, dashboard ₹>0, optimizer, scenario, assistant, telemetry snapshot, reports, role gating).
- `test_engine.py` — unit (ALE=SLE×ARO, control/exposure effects, knapsack, `saturating`, `fmt_inr`, framework bands).
- `test_tenant_isolation.py` — cross-tenant isolation proofs.

### Backend runtime artifacts
- `backend/cyberrisk.db` (SQLite, auto-created), `ml_incident_model.joblib` (model cache), `backend/generated_reports/` (PDFs), `backend/.venv/` (Python 3.14 venv).

---

## Repo-level
- `CLAUDE.md` / `GEMINI.md` — top-level context entry points (identical).
- `docs/` — this documentation set (ARCHITECTURE, BACKEND, FRONTEND, FILE_INDEX, CONVENTIONS, RUNBOOK).
- `.claude/skills/` — `web-dev`, `ui-design`, `context-manager`, `productivity`.
- `_recovery_snapshot_20260929_222809/` — pre-redesign backup. **Do not delete.**

