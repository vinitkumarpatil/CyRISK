# ARCHITECTURE.md — System Design & Data Flow

## Overview
RiskQuant is a two-tier app: a React SPA (Vite) talking to a FastAPI service over `/api`, with SQLite persistence. It quantifies cyber risk in **rupees** using the **FAIR** model (Annualized Loss Expectancy), adds Monte-Carlo Value-at-Risk, a machine-learning likelihood nudge, control-effectiveness scoring, framework mapping, a knapsack investment optimizer, what-if scenarios, and PDF/JSON reports. It is **multi-tenant** with a seeded demo org for presentation.

```
Browser (React SPA :5173)
  │  fetch /api/*  (bearer token in localStorage.sih_token)
  ▼
Vite dev proxy  ──►  FastAPI (:8000)
                       ├─ routers/        validate token, derive org_id (current_org)
                       ├─ deps.py cache   per-org memoized compute (state/result/recs/frameworks)
                       ├─ engine/         FAIR math, VaR, ML, optimizer, scenarios, reports
                       └─ models/ (ORM) ─► SQLite (cyberrisk.db)
```

## Request lifecycle (a data endpoint)
1. SPA calls `api.get('/api/...')`; `client.ts` attaches `Authorization: Bearer <token>`.
2. Vite proxies `/api` → `http://127.0.0.1:8000` (dev). In prod the SPA is served with `VITE_API_BASE` pointing at the API.
3. Router dep chain: `get_current_user` (decode HMAC token → load `User`) → optional `require_roles` → **`current_org`** derives `org_id` from the **server-side user record only**.
4. Router asks `deps.get_state/get_result/...` — a per-org memoized cache. On a miss it builds state from the DB (`engine/state.build_state`) and runs `engine/risk_engine.compute`.
5. Result serialized to JSON (all money already in ₹). SPA renders via typed hooks/components.

## The compute pipeline (`engine/risk_engine.compute`)
For the org's current state (assets, vulns, controls, threats, incidents, assumptions):
1. **Criticality** per asset (`criticality.py`) → 0–100 + tier.
2. **Control effectiveness** per control (`controls.py`) → 0.02–0.99 + rating, dampened by matching historical incidents.
3. For each **active** vuln on an asset (a "finding"):
   - **SLE** = Σ six impact components (`financial.impact_components`).
   - **ARO** = base(sev,cvss) × exposure × age × threat, reduced by control effectiveness, then blended with an ML incident probability (`financial.frequency` + `ml_model`).
   - **ALE** = SLE × ARO (`financial.compute_finding`).
4. **Monte-Carlo VaR** across the finding portfolio (`risk_engine.monte_carlo_var`, 5000 seeded sims, Poisson×lognormal) → var95/var99.
5. **Enterprise risk score** 0–100 (weighted ALE saturation + control weakness + critical-vuln count) → band.
6. **Aggregations**: by asset, by business unit, by category, top contributors, control rollup, framework coverage.

Findings require an active vuln; **an org with assets but no vulns computes ₹0** — expected, not a bug.

## Determinism (important for the demo)
- VaR uses a fixed seed (`VAR_SEED=26105`) → identical numbers each run.
- The ML model trains on a fixed synthetic dataset with `random_state=26105` and is cached to `ml_incident_model.joblib`.
- The NL assistant (`nlq.py`) is fully deterministic and reads numbers only from the computed result — no LLM fabricates figures.

## Decision tools (all reuse the same engine on cloned state)
- **Scenarios** (`scenarios.py`): apply mutation ops (improve/degrade control, patch vulns, reduce exposure, add vuln, change assumption, delay remediation) to a deep-copied state, recompute, and report before/after/delta + ROSI. Never touches the real DB unless explicitly saved.
- **Recommendations** (`recommend.py`): simulate each investment option individually, rank by ALE reduction, attach priority/ROSI/rationale.
- **Optimizer** (`optimizer.py`): 0/1 knapsack picks the best set of options within a budget, then **re-simulates the chosen set jointly** (reductions are non-additive) and reports portfolio ROSI + an efficiency curve.

## Multi-tenancy & auth
- Stdlib HMAC bearer token (`{payload}.{sig}`, 12h TTL); PBKDF2 passwords. See `docs/BACKEND.md`.
- Every business table has `org_id`; `current_org` derives it from the authenticated user, so a client **cannot** cross tenants by passing an `org_id` (proven in `tests/test_tenant_isolation.py`).
- Roles: `executive` (read-only), `ciso` / `analyst` (mutate). Demo `POST /api/demo/load` is restricted to demo orgs (403 otherwise), and seeded demo assets are read-only (403 on edit/delete).

## State invalidation
The per-org compute cache (`deps._CACHE`) is invalidated on: demo reload, telemetry simulation, asset create/update/delete, imports, and assumption edits. On the frontend, mutations dispatch a `risk-refresh` window event; pages using `useApi(path,{refreshOnTelemetry:true})` reload automatically.

## Theming (frontend)
Two themes via CSS-variable semantic tokens. Night is `:root` (default); Day is `.theme-day` on `<html>`. Recharts can't use CSS classes, so charts read a JS palette from `useTheme().chart`. See `docs/FRONTEND.md` and the `ui-design` skill.

## Persistence & artifacts
- `backend/cyberrisk.db` — SQLite, auto-created, seeded on first run.
- `ml_incident_model.joblib` — trained model cache.
- `backend/generated_reports/` — rendered PDF reports.
- `_recovery_snapshot_20260929_222809/` — pre-redesign backup (keep).
