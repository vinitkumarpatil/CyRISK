---
name: productivity
description: Use to plan and sequence work on this project so tasks land safely and are verified — scoping a change, breaking a big task into steps, or deciding what to do next. Invoke for "how should I approach this / plan this feature / what's the safest way to do X". Encodes this repo's safe-change workflow and demo-first priorities.
---

# Productivity & Safe-Change Workflow

## Purpose
Ship changes to a demo-critical app efficiently without regressions. Small, verified steps beat big risky ones.

## When to use
- Before starting any non-trivial change.
- When a request is broad ("improve the dashboard") and needs scoping.
- To decide sequencing across multiple edits.

## Priorities for this project (in order)
1. **Don't break the demo.** The app must always log in and show the seeded "Meghdoot Financial Services Ltd (DEMO)" data.
2. **Respect the backend freeze.** Frontend-only unless explicitly told otherwise; never silently change backend.
3. **Both themes correct.** Every visual change works in Day and Night.
4. **Truthful numbers.** All values come from the backend risk engine; nothing faked client-side.

## Standard task loop
1. **Clarify scope** — restate the goal in one line; identify the smallest change that satisfies it. Don't add features not asked for.
2. **Locate** — use the `web-dev`/`ui-design`/context docs to find exact files (`docs/FILE_INDEX.md` is the map).
3. **Read before writing** — open the target file(s) and match existing patterns (naming, tokens, components).
4. **Change** — make the focused edit. Reuse shared primitives; use semantic tokens; format ₹ via `inr()`.
5. **Type-check** — `cd frontend && npm run typecheck` (must be clean).
6. **Verify in browser** — load the affected screen, check console, test Day + Night (see `web-dev` verification workflow). Backend up on :8000, frontend on :5173.
7. **Build** — `npm run build` succeeds before declaring done.
8. **Update context** — if the change is structural, run the `context-manager` update rules and persist any new decision to memory.

## Decomposing a large request
- Split by **surface**: one page/component at a time; verify each before moving on.
- Split by **layer**: data (types/api) → logic (page state) → presentation (components/styles).
- Parallelize only independent reads/research (use subagents for broad codebase questions); keep edits sequential and verified.
- If an approach fails twice, stop and diagnose the root cause; try a fundamentally different approach rather than patching.

## When a change seems to need the backend
STOP. State exactly what's missing (endpoint/field/behavior) and why the frontend can't do it alone. Offer the safest frontend-only alternative. Do not edit `backend/` without explicit approval.

## Definition of done
- Type-check clean, build clean, verified in browser in both themes, no new console errors (besides the known Recharts `defaultProps` warnings), demo still works, context/memory updated if structural.

## Example
Request: "Redesign the Reports page." → Scope to Reports only → read `src/pages/Reports.tsx` + its endpoints in `docs/BACKEND.md` → restyle using `CardPad`/`SectionTitle`/tokens → typecheck → verify Reports in Day+Night, confirm PDF download still works → build → done. No other page touched, no backend change.
