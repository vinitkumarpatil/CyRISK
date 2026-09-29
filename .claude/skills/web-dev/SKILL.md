---
name: web-dev
description: Use when building, editing, debugging, or reviewing the RiskQuant FRONTEND (React 18 + TypeScript + Vite + Tailwind + Recharts in frontend/). Covers where UI lives, the component library, data flow, and the mandatory verify-in-browser workflow. Invoke for any "change the UI / add a page / fix this button / style this" task.
---

# RiskQuant Frontend Development

## Purpose
Make correct, on-brand changes to the RiskQuant single-page app without breaking the demo or the backend contract. This skill tells you where things live and how to verify a change.

## When to use
- Adding or editing a page, component, chart, table, form, button, or style.
- Debugging a rendering/console/network issue in the SPA.
- Any task touching `frontend/`.

## Ground rules (do not violate)
1. **Backend is FROZEN.** Never change files under `backend/`, API paths, request/response shapes, calculations, DB, auth, or seeded/demo data. If a frontend need seems to require a backend change, STOP and report it — do not silently edit the backend. (See `docs/CONVENTIONS.md`.)
2. **No registration UI.** Registration was intentionally removed. Do not re-add a register/create-org link, route, or form. Login exposes only the 3 demo accounts (exec / ciso / analyst).
3. **All money is ₹ (INR).** Format currency only through `inr()` in `src/lib/format.ts`. Never hand-format money.
4. **No SIH problem-statement IDs** anywhere in visible UI.
5. **Two themes only — Day & Night.** Every new UI must work in both. Use semantic tokens (never hard-code `slate-*`, `bg-white`, `#0b1220`, etc.). See the `ui-design` skill.
6. **Values come from the backend.** Never compute or fake risk/financial numbers client-side.

## Where things live (quick map — full detail in docs/FRONTEND.md)
- **Routes:** `src/App.tsx` (path → page). Provider nesting: `src/main.tsx` (ThemeProvider → BrowserRouter → AuthProvider).
- **App shell (sidebar nav, topbar, logo, Simulate Telemetry, theme toggle, logout):** `src/components/Layout.tsx`. The sidebar `NAV` array is the single source of nav items.
- **Pages:** `src/pages/*.tsx` — one file per route (Dashboard, RiskAnalysis, Assets, Vulnerabilities, Controls, Recommendations, Scenarios, Optimizer, Frameworks, Assumptions, Assistant, ModelCard, DataSources, Reports, Login).
- **Reusable UI primitives** (StatCard, CardPad, SectionTitle, RiskBadge, Money, ProgressBar, Chip, Loading, ErrorState, EmptyState, Explain, Disclaimer): `src/components/ui.tsx`.
- **Charts** (BarCard, DonutCard, LineCard + theme hook): `src/components/charts.tsx`.
- **Sortable table:** `src/components/DataTable.tsx`. **Modal:** `src/components/Modal.tsx`.
- **Formatting helpers** (inr, pct, pctRaw, num, shortDate, band/status chips, chart colors): `src/lib/format.ts`.
- **Data fetching:** `src/lib/useApi.ts` (`useApi<T>(path, { refreshOnTelemetry })`) and `src/api/client.ts` (`api.get/post/del`, token in localStorage `sih_token`).
- **Types:** `src/api/types.ts`.
- **Theme:** `src/theme/ThemeContext.tsx`; tokens/classes in `src/index.css`; token→color mapping in `tailwind.config.js`.
- **Logo asset:** `frontend/public/riskquant-logo.webp`, referenced as `/riskquant-logo.webp` (used in `Layout.tsx` Brand() and `Login.tsx`).

## How to find a specific UI element
1. Identify the page from the URL/screenshot → open `src/pages/<Page>.tsx`.
2. Search that file for the label text of the button/section.
3. If it's a shared widget (badge, stat card, table), it comes from `src/components/ui.tsx`, `charts.tsx`, or `DataTable.tsx` — edit there to change it everywhere.
4. Nav/topbar/logo → `src/components/Layout.tsx`.

## Data flow
`page` → `useApi<T>('/api/...')` → `api.get` (adds bearer token, `/api` proxied to backend :8000 in dev) → render. Mutations use `api.post/del` then call `reload()` and/or `window.dispatchEvent(new CustomEvent('risk-refresh'))` so dependent views recompute. Pages that pass `{ refreshOnTelemetry: true }` auto-reload on the `risk-refresh` event (fired by Simulate Telemetry).

## Verify EVERY previewable change (mandatory)
1. `cd frontend && npm run typecheck` — must be clean (exit 0).
2. Ensure dev server running (Vite :5173, proxies `/api` → :8000). Backend must be up on :8000.
3. In the browser preview: check console for errors (ignore only the known Recharts `defaultProps` deprecation warnings), reload, and confirm the change.
4. Test in **both** Night and Day (toggle in topbar / login).
5. For layout/responsive changes, check a mobile width too.
6. Before finishing: `npm run build` must succeed (the >500 kB chunk-size warning is pre-existing and OK).
Never claim something works unless you actually loaded it in the browser.

## Examples
- "Move the Logout button" → `src/components/Layout.tsx`, topbar section (`btn-ghost` with `LogOut` icon).
- "Change how annual loss is displayed" → the `Money` component and `inr()` in `src/lib/format.ts` (affects all pages).
- "Add a column to the contributors table" → `src/pages/Dashboard.tsx` `contribCols`, rendered by `DataTable`.
- "Style the risk badge" → `RiskBadge` in `src/components/ui.tsx` + `bandChip/bandHex` in `format.ts`.
