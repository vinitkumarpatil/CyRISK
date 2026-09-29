# CONVENTIONS — Coding Rules & Hard Constraints

These are the non-negotiable rules for this repo. Violating a **HARD CONSTRAINT** breaks the demo or the product intent.

## HARD CONSTRAINTS (do not violate)

1. **Backend is FROZEN.** Do not change anything under `backend/`: API paths, request/response shapes, risk/financial calculations, the DB schema, auth, or seeded/demo data. If a frontend need appears to require a backend change, **STOP and report** exactly what's missing (endpoint/field/behavior) and propose the safest frontend-only alternative. Never silently edit the backend.

2. **No registration UI.** Registration was intentionally removed (`Register.tsx` deleted). Do not re-add a register/create-org link, route, or form. `AuthContext.tsx` still exports an unused `register()` and the `/api/auth/register` endpoint still exists on the backend, but **no UI may reach it**. Login exposes only the 3 demo accounts.

3. **All money is ₹ (INR).** Format currency **only** through `inr()` in `src/lib/format.ts`. Never hand-format money, never use `$`/`USD`, never compute currency strings inline.

4. **No SIH problem-statement identifiers** in visible UI — no `SIH26105`, `SIH 26105`, "Problem Statement ID", or any SIH id. (The string may still appear in non-visible metadata like `package.json` description; that's out of scope. Only visible UI must be clean.)

5. **Two themes only — Day & Night.** Every visual change must work in both. Use **semantic tokens** (`bg-surface`, `bg-panel`, `text-fg`, `border-hairline`, …) — never raw `slate-*`, `bg-white`, or hex for surfaces/text/borders. Night is default (`:root`); Day is `.theme-day` on `<html>`. See the `ui-design` skill.

6. **Values come from the backend.** Never compute, estimate, or fake risk/financial numbers client-side. The frontend renders what the API returns.

## Coding conventions

### Frontend (TypeScript / React)
- **TS strict mode** — `tsc --noEmit` must be clean before you're done.
- One page per route in `src/pages/*.tsx`; shared UI in `src/components/`.
- Reuse primitives from `src/components/ui.tsx` (StatCard, CardPad, SectionTitle, RiskBadge, Money, etc.) and charts from `src/components/charts.tsx` — don't reinvent them per page.
- Data fetching via `useApi<T>(path, { refreshOnTelemetry })` (`src/lib/useApi.ts`); mutations via `api.post/api.del` (`src/api/client.ts`), then `reload()` and/or dispatch `new CustomEvent('risk-refresh')`.
- Types live in `src/api/types.ts` — keep them matching the backend response shapes.
- Tailwind + component classes in `src/index.css` (`.card`, `.card-pad`, `.btn-primary`, `.btn-ghost`, `.input`, `.stat-label`, `.link-muted`). Token→color mapping in `tailwind.config.js`.
- Risk color semantics are fixed: Critical=red, High=orange, Medium=amber, Low=green — via `RiskBadge`/`bandChip`/`bandHex`; don't invent per-page color logic.

### Backend (read-only reference — do not edit)
- FastAPI routers under `app/routers/`, each mounted with an `/api/...` prefix in `app/main.py`.
- Multi-tenant: every business table carries `org_id`; routers derive it server-side via `Depends(current_org)` from the bearer token — never trust a client-supplied org id.
- Risk engine math lives in `app/engine/` (FAIR model: ALE = SLE × ARO per finding; VaR via Monte Carlo; optimizer = 0/1 knapsack; ROSI).

## Definition of done
Type-check clean → build clean → verified in the browser in **both** themes with no new console errors (Recharts `defaultProps` warnings excepted) → demo still logs in and shows seeded data → context/memory updated if the change was structural.

## Tooling note
When Write/Edit hit content-size limits, chunk silently and continue — don't switch tools or ask.
