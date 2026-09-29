---
name: ui-design
description: Use when designing or critiquing the RiskQuant visual UI — layout, spacing, color, typography, the Day/Night theme, charts, or making a screen look premium/enterprise. Invoke for "make this look better / design this screen / review the visual hierarchy / pick colors / fix the theme". Enforces the design system so new UI matches the existing product.
---

# RiskQuant UI Design System

## Purpose
Keep the product visually consistent, premium, minimal, and enterprise-grade across both themes. Use this before/while styling any screen and to review designs.

## When to use
- Building or restyling any screen, card, chart, or control.
- A "make it look premium / clean this up / improve hierarchy" request.
- Reviewing a UI change for visual quality and theme correctness.

## The single most important rule: use semantic tokens, never raw colors
Both themes are driven by CSS variables. Night is the default (`:root`), Day is `.theme-day` on `<html>`. Tailwind classes map to these tokens (see `tailwind.config.js` + `src/index.css`). **Never** write `text-slate-*`, `bg-white`, `bg-ink-*`, or hex colors for surfaces/text/borders — they break Day mode.

| Purpose | Token (Tailwind) | Use for |
|---|---|---|
| App background | `bg-surface` | page background |
| Card background | `bg-panel` | cards, sidebar, header |
| Raised/inset fill | `bg-elevated` | inner tiles, inputs |
| Hairline border | `border-hairline` | default separators |
| Stronger border | `border-hairline-strong` | inputs, buttons, chips |
| Hover wash | `bg-hover/[0.06]` etc. | hover states (opacity-based) |
| Primary text | `text-fg` | headings, key numbers |
| Body text | `text-body` | paragraphs, table cells |
| Secondary text | `text-muted` | labels, subtitles |
| Tertiary text | `text-subtle` | captions, hints |
| Accent | `text-accent` / `bg-accent` | links, focus |

Accent palettes (`brand-*`, `risk-*`, amber) and `text-white` (on gradient buttons) are theme-independent and may be used directly.

## Component classes (in src/index.css) — prefer these over ad-hoc styles
- `.card` / `.card-pad` — standard container (use `CardPad` from `ui.tsx`).
- `.btn-primary` — gradient CTA. `.btn-ghost` — secondary/outline button.
- `.input` — text inputs. `.stat-label` — small uppercase muted label.
- `.link-muted` — muted link that turns accent on hover.

## Risk color semantics (do not repurpose)
- Critical = red (`risk-critical`/`risk-high` reds), High = orange, Medium = amber, Low = green.
- Use `RiskBadge`, `bandChip()`, `bandHex()`, `statusChip()` — don't invent per-page color logic.

## Charts
Use `BarCard` / `DonutCard` / `LineCard` from `src/components/charts.tsx`. They read the active theme via `useChartTheme()` so axes/grid/tooltips adapt automatically. Chart series colors come from `CHART_COLORS` / explicit accent hexes. Never hard-code axis/grid colors in a page.

## Layout & spacing conventions
- Page = vertical stack: `className="space-y-6"`.
- Cards: rounded (`rounded-xl`/`rounded-2xl`), `border-hairline`, `bg-panel`, `shadow-card`, internal padding via `CardPad`.
- KPI rows: responsive grid, e.g. `grid grid-cols-2 gap-4 lg:grid-cols-4`.
- Every page opens with a header: `text-2xl font-bold text-fg` title + `text-sm text-muted` subtitle, optionally a `RiskBadge`/action on the right.
- Two charts side by side: `grid gap-4 lg:grid-cols-2`.

## Design review checklist (visual critique)
When reviewing a screen, check in order:
1. **Theme correctness** — toggle Day/Night; no invisible text, no dark-only assumptions, no raw slate/white classes.
2. **Hierarchy** — the most important number/action is largest and highest; secondary info is muted.
3. **Alignment & grid** — consistent gaps (`gap-4`/`space-y-6`), aligned baselines, no orphan widths.
4. **Density** — enough breathing room; avoid cramped tables; right-align numbers.
5. **Consistency** — reuses shared primitives, matches other pages' patterns.
6. **Brand** — accent used sparingly; risk colors only for risk; logo not stretched.
7. **Responsive** — collapses cleanly at mobile widths.
8. **Empty/loading/error states** — present (use `Loading`, `ErrorState`, `EmptyState`).

## Do / Don't
- DO reuse `ui.tsx` primitives and existing spacing rhythm.
- DO keep it minimal: fewer borders, calmer color, clear type scale.
- DON'T add decorative/fake content, marketing bloat, or new fonts/libraries.
- DON'T distort the logo — always `h-auto` with a fixed width, `object-contain` semantics.
- DON'T introduce a color that isn't a token or an existing accent.

## Verify
Always view the result in the browser in BOTH themes (see the `web-dev` skill's verification workflow) before declaring a design done.
