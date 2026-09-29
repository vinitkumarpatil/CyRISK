# CyberRisk Quant Platform — SIH26105

**AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform**
Smart India Hackathon 2026 · AICTE Cyber Security Cell · Theme: Blockchain & Cybersecurity · Category: Software

Translates qualitative *Low / Medium / High* cyber risk into **monetary terms (₹ INR)** by
correlating security telemetry, business-asset criticality and control effectiveness. It
estimates incident **likelihood**, **Expected Annual Loss (ALE)**, **Value-at-Risk (VaR)**,
the **top risk drivers**, cost-effective **mitigations**, and a **budget-constrained investment
plan** — every figure explainable and traceable back to documented inputs.

---

## ⚠️ Integrity & disclaimers (read first)

This is a **decision-support model on synthetic demonstration data**, engineered to be honest:

- **Synthetic data.** The bundled enterprise ("Meghdoot Financial Services Ltd") and all
  telemetry are fictional. Figures are **modelled estimates**, never presented as real-world data.
- **No compliance claim.** Framework mapping (ISO 27001, NIST CSF, CIS, RBI, SEBI) is an
  **assessment aid** using assessment language only — never a claim of certification or compliance.
- **The model owns every number.** The optional LLM in the assistant only *rephrases* a
  deterministic answer; it **never invents financial figures**. All numbers come from the engine.
- **Nothing is hard-coded.** Every headline figure is recomputed from editable assumptions and
  the current state — change an assumption or simulate telemetry and the whole model recomputes.
- **Everything here actually runs.** No fake buttons, mock responses, or static screens.

---

## Architecture

Monorepo with a Python risk engine behind a FastAPI service, and a React/TypeScript SPA.

```
SIH26105/
├── backend/          FastAPI + SQLAlchemy + SQLite, the risk engine, ML model, PDF reports
│   ├── app/
│   │   ├── engine/   risk_engine, financial (SLE/ARO/ALE/VaR), criticality, controls,
│   │   │             ml_model, optimizer (0/1 knapsack), scenarios, nlq, recommend,
│   │   │             snapshots, reports, frameworks_data, state, constants
│   │   ├── routers/  18 route modules (dashboard, risk, assets, vulnerabilities, controls,
│   │   │             recommendations, scenarios, optimizer, frameworks, assumptions,
│   │   │             assistant, model_info, telemetry, reports, imports, investments, auth, demo)
│   │   ├── models/   SQLAlchemy ORM (core, risk, security, frameworks, decisions, users)
│   │   ├── seed/     first-run demo enterprise, catalogs, investment options, vulns
│   │   ├── auth.py   HMAC-signed bearer tokens · config.py · database.py · schemas.py
│   │   └── main.py   app entry: init DB, first-run seed, mount routers
│   └── tests/        pytest — engine math + API contract tests
│
└── frontend/         Vite + React 18 + TypeScript (strict) + Tailwind SPA (~14 pages)
    └── src/
        ├── pages/        Dashboard, Risk, Assets, Vulnerabilities, Controls, Recommendations,
        │                 Scenarios, Optimizer, Investments, Frameworks, Assumptions,
        │                 Assistant, Reports, ModelInfo, Login
        ├── components/   ui kit (Money, Explain, StatCard…), DataTable, Modal, charts, layout
        ├── api/          typed client (bearer auth) + response types
        └── lib/          format (₹ / %), useApi (live telemetry refresh)
```

**Data flow.** SQLite holds the domain state → the engine computes a full risk model on demand →
routers expose typed JSON → the SPA renders it with inline explanations. "Simulate Telemetry"
mutates state and broadcasts a refresh so every open page recomputes and re-renders live.

---

## How it satisfies the problem statement

| Requirement | Where it lives | What it does |
|---|---|---|
| Qualitative → monetary risk | `engine/financial.py` | SLE × ARO = ALE per finding, aggregated to enterprise ₹ |
| Continuous / near-real-time | `routers/telemetry.py`, `engine/snapshots.py` | Simulate telemetry, snapshot the score, trend over time |
| Asset criticality | `engine/criticality.py` | Transparent 0–100 blend of value, downtime, sensitivity, ops, regulatory |
| Control effectiveness | `engine/controls.py` | Per-control coverage reduces likelihood/impact, shown in the math |
| Genuine ML | `engine/ml_model.py` | scikit-learn GradientBoosting (seed 26105) for incident likelihood, hybrid with formulas |
| Top risk drivers | `engine/risk_engine.py` | Ranked contributors by ₹ impact, per asset / BU / category |
| AI mitigations | `engine/recommend.py` | Cost-effective controls ranked by ROSI and ₹ risk reduced |
| What-if simulator | `engine/scenarios.py` | Re-runs the full model with chosen controls; real before/after |
| Investment optimization | `engine/optimizer.py` | 0/1 knapsack under a ₹ budget; picks change with budget/inputs |
| ROSI & cost-benefit | `engine/optimizer.py`, Investments page | ROSI %, payback, investment-vs-risk-reduction curve |
| NL query interface | `engine/nlq.py`, `routers/assistant.py` | Deterministic intent parser over the model; LLM only rephrases |
| Executive + technical views | Dashboard / ModelInfo pages | Role-aware summary vs. full derivation and feature vectors |
| Framework mapping | `engine/frameworks_data.py` | ISO 27001, NIST CSF, CIS, RBI, SEBI — assessment language only |
| Evidence-based reporting | `engine/reports.py`, `routers/reports.py` | Real PDF/JSON reports generated from live state |

---

## Quick start

**Prerequisites:** Python 3.11+ and Node 18+.

### 1. Backend (FastAPI, port 8000)

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY to any random string
uvicorn app.main:app --reload --port 8000
```

On first launch the app **auto-creates the SQLite DB and seeds the fictional demo enterprise**
(no manual migration or seed step). The scikit-learn model trains deterministically on first use.

> **Windows console tip:** to print the ₹ symbol in logs, prefix the command with
> `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`. This does not affect the API or the UI.

API docs are then at `http://127.0.0.1:8000/docs`; health at `/api/health`.

### 2. Frontend (Vite + React, port 5173)

```bash
cd frontend
npm install
npm run dev                   # dev server proxies /api → http://127.0.0.1:8000
```

Open `http://127.0.0.1:5173`. For a production bundle: `npm run build` (output in `frontend/dist`).

### Demo accounts

| Username | Password | Role | Can mutate? |
|---|---|---|---|
| `exec` | `exec123` | Executive | No — read-only board view |
| `ciso` | `ciso123` | CISO | Yes |
| `analyst` | `analyst123` | Analyst | Yes |

Mutations (simulate telemetry, run scenarios, edit assumptions, generate reports) require
`ciso`/`analyst`; the executive role is intentionally read-only (returns 403 on writes).

---

## The risk model (how a ₹ figure is built)

Every headline number is derived, never stored as a constant:

1. **Single Loss Expectancy (SLE)** — per finding, from the affected asset's exposed value
   (records × cost-per-record, downtime cost/day, response & regulatory penalties), scaled by the
   asset's **criticality** (0–100 blend of business value, revenue-at-risk, data sensitivity,
   operational and regulatory weight — each factor and its contribution is shown in the UI).
2. **Annual Rate of Occurrence (ARO)** — incident **likelihood**, produced by the hybrid ML model:
   a scikit-learn `GradientBoostingClassifier` (fixed seed **26105**) combined with transparent
   formula adjustments for control coverage and exposure.
3. **Annualized Loss Expectancy (ALE) = SLE × ARO**, summed across findings → enterprise ALE.
4. **Value-at-Risk (VaR₉₅ / VaR₉₉)** — from a loss distribution over the annualized events, so the
   tail (a bad year) is quantified, not just the average.
5. **Controls** reduce likelihood and/or impact by their measured effectiveness; **scenarios** and
   the **optimizer** re-run this whole pipeline to show real before/after deltas and ROSI.

The **assumptions** page exposes the editable drivers (cost per record, downtime cost, etc.).
Change one and every dependent figure recomputes — nothing is hard-coded.

## Feature tour

- **Dashboard** — executive headline ₹ (ALE, exposure, VaR), risk score & band, top contributors,
  breakdown by business unit / category, weakest controls, framework coverage, trend.
- **Risk / Assets / Vulnerabilities / Controls** — drill into each object with its full derivation.
- **Recommendations** — ranked mitigations by ₹ risk reduced and ROSI.
- **Scenarios** — pick controls, run a real what-if, see ALE/VaR/score deltas.
- **Optimizer** — 0/1 knapsack: best control portfolio under a ₹ budget (picks change with budget).
- **Investments** — cost-benefit + investment-vs-risk-reduction curve.
- **Frameworks** — ISO 27001 / NIST CSF / CIS / RBI / SEBI assessment mapping (assessment language).
- **Assumptions** — edit the model's cost drivers; everything recomputes.
- **Assistant** — ask in plain language; a deterministic parser answers from the model.
- **Reports** — generate and download real PDF/JSON evidence reports.
- **Model Info** — the ML model card, feature importances and per-asset feature vectors.

---

## Data import & sample data

Beyond the seeded demo, `ciso`/`analyst` can import their own inventory. Ready-made examples live
in [`sample_data/`](sample_data/) (CSV and JSON for assets and vulnerabilities). Uploads are
size-limited (`MAX_UPLOAD_BYTES`), validated and sanitized before they touch the model.

## Testing & verification

```bash
# Backend — engine math + API contract tests
cd backend && pytest -q

# Frontend — strict type check and production build
cd frontend && npx tsc --noEmit && npm run build
```

Both suites pass and the app has been verified end-to-end in the browser: every page renders
against the live backend, and the optimizer, scenario simulator, assistant, telemetry refresh and
PDF report download were each confirmed to perform real computation — not mock responses.

## Security notes

- **Auth:** HMAC-signed bearer tokens; role-gated mutations (executive is read-only).
- **Secrets:** never committed — `SECRET_KEY` and any LLM key come from `.env` (see `.env.example`).
  The optional LLM is **off by default** (`LLM_ENABLED=false`) and, even when on, only rephrases —
  it is never given the ability to produce a number.
- **Input safety:** Pydantic v2 validation, parameterized ORM queries (no string-built SQL),
  bounded/validated file uploads.
- `.gitignore` excludes `.env`, the SQLite DB, the trained model artifact, `node_modules` and `dist`.

## Tech stack

**Backend:** Python · FastAPI · SQLAlchemy 2 · SQLite · Pydantic v2 · scikit-learn · reportlab · pytest
**Frontend:** Vite · React 18 · TypeScript (strict) · Tailwind CSS · React Router · Recharts · lucide-react

---

*Built for Smart India Hackathon 2026 (SIH26105). All data is synthetic and for demonstration only.*
