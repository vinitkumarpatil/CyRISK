# BACKEND.md — FastAPI Service Reference (FROZEN)

> **Reference only. Do NOT edit `backend/`** (APIs, calculations, DB, auth, seed). See `docs/CONVENTIONS.md`.
> Stack: FastAPI 0.141 + SQLAlchemy 2.1 + Pydantic 2.13, SQLite (`cyberrisk.db`), numpy/scipy/scikit-learn, reportlab. Python 3.14.

## Startup & DB (`app/main.py`, `app/database.py`)
- `lifespan(app)`: `init_db()` → open session → if no `Organization` exists, `seed_demo(db)` (first-run full demo seed) else `_ensure_users(db)` → close → `yield`.
- `init_db()`: imports models, `Base.metadata.create_all(engine)` (creates tables, never ALTERs), then `_migrate_lightweight()` (additive back-fill: adds nullable `users.org_id` on legacy DBs — the only migration logic).
- Engine: `create_engine(DATABASE_URL, connect_args={"check_same_thread": False} for sqlite, future=True)`. `get_db()` FastAPI dependency yields a session.
- Two public meta routes on `app` (no auth): `GET /` (metadata + disclaimer), `GET /api/health`.

## Router registration (`app/main.py` + `app/routers/__init__.py`)
Routers carry **no** prefix from `main.py` — it just loops `app.include_router(r)` over `ALL_ROUTERS`. Each router sets its own `/api/...` prefix. Prefix map:

| Router | Prefix | Router | Prefix |
|---|---|---|---|
| auth | `/api/auth` | investments | `/api/investments` |
| demo | `/api/demo` | optimizer | `/api/optimizer` |
| dashboard | `/api/dashboard` | frameworks | `/api/frameworks` |
| risk | `/api/risk` | recommendations | `/api/recommendations` |
| assets | `/api/assets` | assistant | `/api/assistant` |
| vulnerabilities | `/api/vulnerabilities` | model_info | `/api/model` |
| controls | `/api/controls` | assumptions | `/api/assumptions` |
| telemetry | `/api/telemetry` | reports | `/api/reports` |
| scenarios | `/api/scenarios` | imports | `/api/imports` |

## Auth & multi-tenancy (`app/auth.py`, `app/deps.py`)
- **Token:** stdlib HMAC-signed (not JWT): `"{payload_b64}.{sig}"`, payload `{sub,username,role,exp}`, `exp` = now + `TOKEN_TTL_HOURS` (12h). `sig` = base64(HMAC-SHA256(`SECRET_KEY`, payload_b64)). `decode_token` verifies with `hmac.compare_digest`, rejects on expiry.
- **Passwords:** PBKDF2-HMAC-SHA256, 120k iters, 16-byte salt → `"pbkdf2${iters}${salt_hex}${hash_hex}"`.
- **Deps:** `get_current_user` (requires `Authorization: Bearer`, 401 on failure) → `require_roles(*roles)` (403 factory) → **`current_org(user) -> int`** derives `org_id` **strictly from the server-side user record** (`user.org_id`), never from client input. This is the tenant-isolation keystone: a client cannot reach another tenant by supplying an `org_id`.
- **Compute cache (`deps.py`):** per-org memo `_CACHE` (RLock-guarded) with `invalidate(org_id)`, builders `get_state`/`get_result`/`get_recommendations`/`get_frameworks`, `options_for(db, org_id)`. Invalidated on demo reload, telemetry sim, asset CRUD, imports, assumption edits.

## Risk engine (`app/engine/`) — real formulas
- **SLE** (`financial.impact_components`): sum of six components — asset business impact (`business_value × EF`, EF capped 0.95), downtime cost (`revenue/day × SEVERITY_DOWNTIME_DAYS`), data-breach cost (`records × cost/record × sensitivity/5 × sf`), recovery, regulatory penalty, reputation. `sf` = severity factor (Crit 1.0 / High .75 / Med .45 / Low .2).
- **ARO** (`financial.frequency`): `base(sev, cvss) × exposure_mult(internet 1.8, exploit 1.6, no-patch 1.3) × age_mult × threat_mult`, reduced by controls (`×(1 − 0.85·control_eff)`), then ML blend `×(0.70 + 0.60·ml_prob)`. `annualized_likelihood = 1 − e^(−aro)` (Poisson P≥1).
- **ALE** (`financial.compute_finding`): `ALE = round(SLE × ARO, 2)`. A finding requires an **active** vuln (`status ∈ {open, remediating}`); no vulns → ₹0.
- **VaR** (`risk_engine.monte_carlo_var`): 5000 sims, `Poisson(aro) × SLE × lognormal(σ=0.5)` summed per portfolio; returns `var95/var99/mean/p50`. Seeded (`VAR_SEED=26105`) → deterministic.
- **Enterprise score 0–100** (`risk_engine._risk_score`): `0.75·ale_comp + 0.15·ctrl_comp + 0.10·critvuln_comp`. Bands: Critical≥75, High≥50, Medium≥25, else Low.
- **Optimizer** (`optimizer.optimize`): 0/1 knapsack DP over options (cost in lakhs, value = marginal ALE reduction), then the selected portfolio is **jointly re-simulated** (non-additive) → `joint_ale_reduction_inr/pct`, `portfolio_rosi_percent`, plus an efficiency `curve`.
- **ROSI** (`scenarios.rosi_percent`): `(ale_reduction − cost) / cost × 100` (None if cost 0).
- **ML** (`ml_model`): `GradientBoostingClassifier` (180 trees, depth 3, lr .08, seed 26105) trained on a 4000-row synthetic dataset, persisted to `ml_incident_model.joblib`. Outputs `ml_prob` that only **nudges ARO** — never sets money. `explain()` gives directional attribution.

Other engine modules: `controls` (effectiveness scoring), `criticality` (asset 0–100 + tier), `frameworks_data` (coverage/assessment, not certification), `nlq` (deterministic NL router — numbers always from computed result, no LLM invention), `recommend` (re-simulate each option, rank by ALE reduction), `reports` (JSON payload + reportlab PDF), `scenarios` (what-if on cloned state + mutation ops), `snapshots` (persist result → RiskSnapshot/Finding/Contribution), `state` (DB → in-memory dict, `clone_state`), `constants` (all tunables), `__init__` (`clamp`, `saturating`, `fmt_inr`, …).

## Endpoints by router (● = mutates data)
**auth** — ● `POST /register` (create org+admin), `POST /login`, `GET /me`, `GET /demo-users`.
**demo** — `GET /status`; ● `POST /load` (reseed, **403 unless caller org is_demo**); ● `POST /simulate-telemetry` (mutate + recompute + snapshot; fires nothing server-side but frontend dispatches `risk-refresh`).
**dashboard** — `GET /` (one-call rollup: metrics, headline ₹, contributors, by BU/category, weak controls, top assets, framework coverage, ml card, trend, role).
**risk** — `GET /`, `/enterprise`, `/findings?limit=`, `/contributors`, `/snapshots`, `/trend`.
**assets** — ● `POST /` (ciso/analyst), `GET /`, `GET /{id}`, ● `PUT /{id}`, ● `DELETE /{id}`. `_owned_asset` guard: 404 foreign/missing, 403 on demo assets.
**vulnerabilities** — `GET /` (ALE/likelihood annotations + by_severity/by_status counts).
**controls** — `GET /`, `GET /{key}`.
**telemetry** — `GET /` (simulated connector list).
**scenarios** — ● `POST /simulate` (mutations on cloned state; save optional), ● `POST /investment` (by option key; save optional), `GET /`. (Compute is read-only; writes a `Scenario` only if `save:true`.)
**investments** — `GET /` (per-option marginal ALE reduction + ROSI), `GET /recommendations`.
**optimizer** — `POST /run` (knapsack; any authed user; no persistence).
**frameworks** — `GET /`, `GET /{key}`.
**recommendations** — `GET /` (ranked mitigations + summary).
**assistant** — `POST /query` (deterministic `nlq.answer`), `GET /suggestions`.
**model_info** — `GET /model` (ML card; depends on `get_current_user` only, **not** `current_org` — global, no tenant data).
**assumptions** — `GET /`, ● `PUT /` (update by key; ciso/analyst; 400 if not editable).
**imports** — `GET /template/{kind}`; ● `POST /{kind}` (CSV/JSON upload; ciso/analyst; extension allow-list, byte/row caps, per-field validation, ORM-only).
**reports** — ● `POST /generate` (build payload + Report row; PDF to disk if fmt=pdf), `GET /`, `GET /{id}`, `GET /{id}/download` (FileResponse for pdf else JSON).

## Data model (`app/models/`) — tables & tenancy
Every business table has `org_id → organizations.id` (NOT NULL) **except**: `users.org_id` (nullable, indexed); child tables inheriting tenancy via parent (`asset_dependencies`, `control_assessments`); and the **global** framework catalog (`frameworks`, `framework_controls` — no org_id). `framework_mappings` **is** org-scoped.

- **core.py:** `organizations` (the tenant — no org_id), `business_units`, `business_services`, `assets` (business_value_inr, revenue_impact_per_day_inr, data_sensitivity 0–5, criticality/regulatory 0–5, records_count, internet_facing…), `asset_dependencies`.
- **security.py:** `vulnerabilities` (cvss, severity, exploit_available, internet_exposed, status, patch_available, age_days…), `threats`, `incidents`, `controls` (config_strength, coverage, compliance_status, maturity 0–5, monitored), `control_assessments`, `telemetry_sources`.
- **risk.py:** `financial_assumptions` (key/value/editable), `risk_snapshots` (score, total_ale_inr, var95/99, JSON rollups), `risk_findings` (sle_inr, aro, ale_inr, breakdown JSON), `risk_contributions`.
- **decisions.py:** `mitigation_actions`, `investment_options` (key, action, cost_inr, params JSON), `scenarios` (spec/result JSON), `recommendations` (rosi, expected_ale_reduction_inr, rationale JSON), `reports` (kind, fmt, payload JSON, file_path).
- **frameworks.py:** `frameworks` (global), `framework_controls` (global), `framework_mappings` (org-scoped, status default "Review Required").
- **users.py:** `users` (org_id nullable, username unique, password_hash, role ∈ executive/ciso/analyst).

## Seed (`app/seed/`)
`loader.seed_demo(db)` builds the fictional **"Meghdoot Financial Services Ltd (DEMO)"** (Banking & Financial Services): 6 BUs, 9 services, **22 assets**, 23 dependency edges, ~45 vulns (real public CVE ids for realism), 7 incidents, 10 controls, 7 threats, telemetry sources, financial assumptions, 14 investment options, 5 frameworks (iso27001, nist_csf, CIS, RBI, SEBI) with controls + mappings (start "Review Required"), then `_ensure_users`. `DEMO_USERS`: exec/exec123 (executive), ciso/ciso123 (ciso), analyst/analyst123 (analyst). `reset_demo` deletes in FK-safe order.

## Tests (`backend/tests/`)
`conftest.py` points `DATABASE_URL` at a temp SQLite file before import; `client` fixture (TestClient triggers lifespan seed); role-header fixtures. `test_api.py` (integration: auth, read endpoints 200, dashboard >0 ₹, optimizer deterministic/budget, scenario recompute, assistant sourced + "2 crore"→20,000,000, telemetry snapshot, report JSON+PDF magic, role gating). `test_engine.py` (unit: ALE=SLE×ARO, control/exposure effects, knapsack optimality, `saturating`, `fmt_inr`, framework bands). `test_tenant_isolation.py` (cross-tenant 404s, client `org_id` override ignored, demo read-only 403, register isolation, duplicate username 409).

## Config (`app/config.py`)
`DATABASE_URL` (default sqlite `cyberrisk.db`), `SECRET_KEY` (dev default — change in prod), `TOKEN_TTL_HOURS=12`, `CORS_ORIGINS`, `MAX_UPLOAD_BYTES=10MB`, `ALLOWED_UPLOAD_EXT={.csv,.json}`, `CURRENCY`/`CURRENCY_SYMBOL` (₹). LLM disabled by default.
