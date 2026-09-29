---
name: context-manager
description: Use at the START of a new session to load project context fast, and at the END (or after any structural change) to keep the context files accurate. Invoke for "get up to speed / what is this project / update the docs / I added a page, update context". Keeps CLAUDE.md, GEMINI.md, and docs/ in sync with the code.
---

# Context Manager

## Purpose
Let any new chat pick up this project without re-explaining it, and keep the written context truthful as the code changes.

## When to use
- First thing in a fresh session (bootstrap).
- After adding/removing/renaming a page, route, component, router, endpoint, model, or engine module.
- After a decision that isn't obvious from the code (a constraint, a "why we did it this way").

## Bootstrap sequence (start of session)
Read, in order:
1. `CLAUDE.md` (root) — overview, stack, rules, quick map. (`GEMINI.md` is identical.)
2. `docs/FILE_INDEX.md` — every file → purpose + "where do I change X".
3. The area doc for the task: `docs/FRONTEND.md`, `docs/BACKEND.md`, or `docs/ARCHITECTURE.md`.
4. `docs/CONVENTIONS.md` (rules/constraints) and `docs/RUNBOOK.md` (how to run/test/build).
Then confirm current state with a quick `git`-free check (files exist, server runs) rather than trusting memory.

## The context file map
- `CLAUDE.md` / `GEMINI.md` — top-level entry points (keep them identical). Overview, architecture summary, tech stack, run commands, hard rules, compact repo map, links to `docs/`.
- `docs/ARCHITECTURE.md` — system design, data flow, the risk engine and formulas.
- `docs/FRONTEND.md` — pages, components, "where does this UI live", theming.
- `docs/BACKEND.md` — routers→endpoints, engine modules, models, seed.
- `docs/FILE_INDEX.md` — exhaustive file-by-file index.
- `docs/CONVENTIONS.md` — coding conventions + hard constraints (backend freeze, ₹, themes, no registration/SIH).
- `docs/RUNBOOK.md` — install, run, test, build, common tasks, troubleshooting.
- `.claude/skills/*/SKILL.md` — task workflows (web-dev, ui-design, context-manager, productivity).

## Update rules (keep docs true)
- When you add a **page/route**: update `src/App.tsx` map in `docs/FRONTEND.md`, the `NAV` note if it appears in the sidebar, and `docs/FILE_INDEX.md`.
- When you add a **component/primitive**: add it to `docs/FRONTEND.md` component list and `FILE_INDEX.md`.
- When you add/remove an **endpoint or router**: update `docs/BACKEND.md` and `FILE_INDEX.md`.
- When a **constraint or decision** changes: update `docs/CONVENTIONS.md` AND the persistent memory file (`C:\Users\vtkr5\.claude\projects\C--Users-vtkr5-Desktop-SIH26105\memory\sih26105-project.md`) so it survives across sessions.
- Keep `CLAUDE.md` and `GEMINI.md` byte-for-byte identical — edit one, copy to the other.
- Prefer editing the existing doc over creating a new one. Docs describe *where* and *why*; they should not duplicate large code blocks (link to the file instead).

## Anti-drift checklist (run at end of a structural task)
1. Did I add/move/delete a file? → Is `docs/FILE_INDEX.md` still correct?
2. New feature? → Is it findable via "where does X live"?
3. New rule/decision? → Captured in `CONVENTIONS.md` + memory?
4. `CLAUDE.md` == `GEMINI.md`?

## Example
User: "I added a Compliance page at /compliance." → update: `docs/FRONTEND.md` (route table + page section), `docs/FILE_INDEX.md` (new `src/pages/Compliance.tsx` row), and if it's in the sidebar, note the new `NAV` entry. Then re-verify the routes list matches `src/App.tsx`.
