# FRONTEND.md — React SPA Reference ("where does this UI live")

> Stack: Vite 5.4 + React 18.3 + TypeScript 5.6 (strict) + Tailwind 3.4 + Recharts 2.12 + lucide-react + react-router-dom 6. Root: `frontend/`.
> Rules: backend frozen, no registration UI, ₹ via `inr()`, no SIH IDs, two themes. See `docs/CONVENTIONS.md`.

## Boot & providers
- `src/main.tsx` — mounts `#root`: `StrictMode → ThemeProvider → BrowserRouter → AuthProvider → App`. Imports `./index.css`.
- `src/App.tsx` — the router (below). `RequireAuth` guard reads `useAuth()`: while `loading` shows `<Loading label="Restoring session…" />`; if no `user`, redirects to `/login`.
- `src/index.css` — Tailwind layers + **semantic theme tokens** and component classes (`.card`, `.card-pad`, `.btn-primary`, `.btn-ghost`, `.input`, `.chip`, `.stat-label`, `.link-muted`); `.theme-day` overrides the token variables for Day mode.
- `index.html` — title **"RiskQuant"**, favicon = `/riskquant-logo.webp`.

## Route table (`src/App.tsx`)
`/login` is public (outside the shell). Everything else is `RequireAuth → Layout` (shared shell with `<Outlet/>`):

| Path | Page file | Sidebar label |
|---|---|---|
| `/login` | `pages/Login.tsx` | — (public) |
| `/` (index) | `pages/Dashboard.tsx` | Dashboard |
| `/risk` | `pages/RiskAnalysis.tsx` | Risk Analysis |
| `/assets` | `pages/Assets.tsx` | Assets |
| `/vulnerabilities` | `pages/Vulnerabilities.tsx` | Vulnerabilities |
| `/controls` | `pages/Controls.tsx` | Controls |
| `/recommendations` | `pages/Recommendations.tsx` | Recommendations |
| `/scenarios` | `pages/Scenarios.tsx` | What-if Scenarios |
| `/optimizer` | `pages/Optimizer.tsx` | Investment Optimizer |
| `/frameworks` | `pages/Frameworks.tsx` | Frameworks |
| `/assumptions` | `pages/Assumptions.tsx` | Assumptions |
| `/assistant` | `pages/Assistant.tsx` | Risk Assistant |
| `/model` | `pages/ModelCard.tsx` | ML Model |
| `/telemetry` | `pages/DataSources.tsx` | Data Sources |
| `/reports` | `pages/Reports.tsx` | Reports |
| `*` | `<Navigate to="/" replace/>` | — (redirects to Dashboard, **not** login) |

Note the label↔path mismatches: `/scenarios`="What-if Scenarios", `/optimizer`="Investment Optimizer", `/assistant`="Risk Assistant", `/model`="ML Model", `/telemetry`="Data Sources" (file `DataSources.tsx`).

## App shell (`src/components/Layout.tsx`)
- **Sidebar `NAV`** (single source of nav items) grouped in this order: `Overview` (Dashboard `/` `LayoutDashboard`, Risk Analysis `/risk` `Activity`), `Inventory` (Assets `/assets` `Server`, Vulnerabilities `/vulnerabilities` `ShieldAlert`, Controls `/controls` `ShieldCheck`), `Decisions` (Recommendations `/recommendations` `Lightbulb`, What-if Scenarios `/scenarios` `GitBranch`, Investment Optimizer `/optimizer` `SlidersHorizontal`), `Governance` (Frameworks `/frameworks` `BookMarked`, Assumptions `/assumptions` `Settings2`), `Intelligence` (Risk Assistant `/assistant` `Bot`, ML Model `/model` `BrainCircuit`), `Operations` (Data Sources `/telemetry` `Radio`, Reports `/reports` `FileText`). Icons from lucide-react, `h-4 w-4`. Dashboard uses `end` so it only highlights on exact match.
- **Topbar** (right side, in order): **Simulate Telemetry** button (only for `ciso`/`analyst` — `POST /api/demo/simulate-telemetry`, then dispatches `risk-refresh`), **ThemeToggle** (Day/Night, Moon/Sun), **user chip** (name + role, `sm:flex`), **Logout** (`LogOut` icon).
- **Left header:** mobile menu button, org name (`user.organization` or `GET /api/demo/status` fallback), "Demo" pill when `user.is_demo`, subtitle "Continuous Cyber Risk Quantification".
- **`Brand()`** renders the logo `<img src="/riskquant-logo.webp" alt="RiskQuant" />` (Layout.tsx:181).

## Reusable primitives (`src/components/ui.tsx`)
`Card`, `CardPad` (padded card), `SectionTitle` (title + optional subtitle + right slot), `StatCard` (KPI tile: label/value/sub/accent/icon), `Money` (renders `inr()` in tabular-nums), `RiskBadge` (chip via `bandChip`), `Chip`, `ProgressBar` (0–1 fraction), `Loading` (spinner), `ErrorState` (with retry), `EmptyState`, `Disclaimer` (synthetic-data notice, tone adapts to theme), `Explain` (collapsible "How this is calculated"). Also re-exports `inr`, `pct`. **Reuse these — don't reinvent per page.**

## Charts (`src/components/charts.tsx`)
`BarCard` (vertical/horizontal), `DonutCard` (Pie), `LineCard` (line/area). A local `useChartTheme()` reads `useTheme().chart` to feed Recharts JS color props (axis/grid/tooltip/legend/cursor) — never hard-code axis/grid colors. Money tooltips/axes use `inr()`; series colors default to `CHART_COLORS`.

Also: `src/components/DataTable.tsx` (sortable table), `src/components/Modal.tsx`.

## Formatting (`src/lib/format.ts`)
`inr(amount)` (₹ Cr/L/K, nullish→'₹0'), `pct(x, digits=1)` (x is a 0–1 fraction), `pctRaw(x)` (x already a %), `num(x)` (`en-IN` locale), `shortDate(iso)`, `bandChip(band)` (Tailwind classes), `bandHex(band)` (Critical `#f43f5e`/High `#fb923c`/Medium `#fbbf24`/Low `#34d399`), `statusChip(status)`, `CHART_COLORS` (8-color array). `type Band`.

## Theme (`src/theme/ThemeContext.tsx`)
`type Theme = 'day'|'night'`. Applied as `root.classList.toggle('theme-day', theme==='day')` on `document.documentElement`. Night is default (no class). localStorage key **`sih_theme`** (default `night`). Context `{ theme, toggle, setTheme, chart }` where `chart` is the theme-aware Recharts palette (`NIGHT_CHART`/`DAY_CHART`: axis/grid/tooltipBg/tooltipBorder/tooltipLabel/tooltipItem/legend/cursor). `CHART_COLORS` (series colors) lives in `format.ts`, separate from this palette.

## Data flow
- `src/lib/useApi.ts` — `useApi<T>(path, { refreshOnTelemetry? })` → `{ data, loading, error, reload }`. Skips if `path === null`. With `refreshOnTelemetry`, subscribes to the window `risk-refresh` event and re-loads (event fired by Simulate Telemetry in Layout and by DataSources).
- `src/api/client.ts` — base `import.meta.env.VITE_API_BASE` (blank in dev → Vite proxies `/api`). Bearer attached via `authHeaders()`; token key **`sih_token`**. On **401 it clears the token** (returns to login). Helpers: `get`, `post`, `put`, `del`, `upload` (multipart `file`), `download` (blob + browser save, parses `content-disposition`). Exports `ApiError{status,detail}` and bundled `api`.
- `src/auth/AuthContext.tsx` — `{ user, loading, login, register, logout }`. `GET /api/auth/me` (restore), `POST /api/auth/login`, `GET /api/auth/demo-users` (via `fetchDemoUsers`). `register()`/`RegisterBody` + `/api/auth/register` **exist but are unreachable from any UI** (kept intentionally; do not surface).
- `src/api/types.ts` — all response interfaces (User, Dashboard, RiskResult, Finding, ControlOut, Framework, OptimizeResult, Recommendation, InvestmentOption, Assumption, ScenarioResult, AssistantAnswer, …).

## Pages → endpoints
- **Dashboard** — `useApi('/api/dashboard', {refreshOnTelemetry:true})`.
- **RiskAnalysis** — `useApi('/api/risk', {refreshOnTelemetry:true})` (SLE→ARO→ALE derivation + VaR).
- **Assets** — `useApi('/api/assets', …)`; `get('/api/assets/{id}')`; ● `post('/api/assets')`, ● `put('/api/assets/{id}')`, ● `del('/api/assets/{id}')`.
- **Vulnerabilities** — `useApi('/api/vulnerabilities', …)` (read-only).
- **Controls** — `useApi('/api/controls', …)`.
- **Recommendations** — `useApi('/api/recommendations', …)` (ROSI + rationale).
- **Scenarios** — `get('/api/investments')`; ● `post('/api/scenarios/investment')` (before/after deltas).
- **Optimizer** — ● `post('/api/optimizer/run', {budget_inr})` (knapsack + efficient frontier).
- **Frameworks** — `useApi('/api/frameworks', …)` (ISO/NIST/CIS/RBI/SEBI assessment aid).
- **Assumptions** — `get('/api/assumptions')`; ● `put('/api/assumptions', {key,value})`.
- **Assistant** — `get('/api/assistant/suggestions')`; ● `post('/api/assistant/query', {question})` (deterministic).
- **ModelCard** — `useApi('/api/model', …)` (ML model card).
- **DataSources** (route `/telemetry`) — `useApi('/api/telemetry', …)`, `useApi('/api/risk/snapshots', …)`, ● `post('/api/demo/simulate-telemetry')`.
- **Reports** — `get('/api/reports')`; ● `post('/api/reports/generate', {kind,fmt,budget_inr})`; `api.download('/api/reports/{id}/download')`.
- **Login** — via AuthContext: `GET /api/auth/demo-users`, `POST /api/auth/login`. Split layout, 3 demo quick-fill cards, theme toggle. No register UI.

## How to find a UI element
1. URL/screenshot → open the matching `src/pages/<Page>.tsx`; search for the label text.
2. Shared widget (badge, stat card, table, chart) → edit in `components/ui.tsx`, `charts.tsx`, or `DataTable.tsx` (changes it everywhere).
3. Nav / topbar / logo → `components/Layout.tsx`.
4. Money format → `Money` + `inr()` in `lib/format.ts`. Theme colors → `index.css` tokens + `tailwind.config.js`.

## Confirmed clean
No registration page/route; no `SIH26105`/`SIH 26105`/`Problem Statement` text anywhere in `src`. Logo referenced only as `/riskquant-logo.webp` in `components/Layout.tsx:181`, `pages/Login.tsx:57`, `pages/Login.tsx:89` (asset lives in `frontend/public/`).
