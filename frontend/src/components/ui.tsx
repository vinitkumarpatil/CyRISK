// Shared UI primitives used across every page. Kept presentational and typed;
// all monetary values flow through <Money> so formatting stays consistent.
// Colours use semantic theme tokens (fg/body/muted/panel/hairline …) so every
// primitive adapts to Day/Night automatically.

import { ReactNode, useState } from 'react'
import { ChevronDown, Info, AlertTriangle, Loader2 } from 'lucide-react'
import { inr, pct, bandChip } from '../lib/format'
import { useTheme } from '../theme/ThemeContext'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>
}
export function CardPad({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card card-pad ${className}`}>{children}</div>
}

export function SectionTitle({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        <h2 className="text-lg font-semibold text-fg">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
      </div>
      {right}
    </div>
  )
}

export function StatCard({
  label, value, sub, accent, icon,
}: { label: string; value: ReactNode; sub?: ReactNode; accent?: string; icon?: ReactNode }) {
  return (
    <div className="card card-pad">
      <div className="flex items-start justify-between">
        <div className="stat-label">{label}</div>
        {icon && <div className="text-subtle">{icon}</div>}
      </div>
      <div className={`mt-2 text-2xl font-bold tracking-tight ${accent ?? 'text-fg'}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-muted">{sub}</div>}
    </div>
  )
}

/** Renders an INR amount consistently (crore/lakh convention). */
export function Money({ v, className = '' }: { v: number | null | undefined; className?: string }) {
  return <span className={`tabular-nums ${className}`}>{inr(v)}</span>
}

export function RiskBadge({ band }: { band: string }) {
  return <span className={`chip ${bandChip(band)}`}>{band}</span>
}

export function Chip({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <span className={`chip ${className}`}>{children}</span>
}

export function ProgressBar({ value, color = 'bg-brand-500' }: { value: number; color?: string }) {
  const w = Math.max(0, Math.min(100, value * 100))
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-hover/10">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${w}%` }} />
    </div>
  )
}

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-muted">
      <Loader2 className="h-5 w-5 animate-spin" /> {label}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card card-pad flex flex-col items-center gap-3 py-12 text-center">
      <AlertTriangle className="h-8 w-8 text-risk-high" />
      <div className="text-body">{message}</div>
      {onRetry && <button className="btn-ghost" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return <div className="py-10 text-center text-sm text-subtle">{message}</div>
}

/** Standing disclaimer — synthetic demo data, assessment (not certification). */
export function Disclaimer({ text }: { text?: string }) {
  const { theme } = useTheme()
  const tone = theme === 'day' ? 'text-amber-700' : 'text-amber-200/80'
  return (
    <div className={`mt-6 flex items-start gap-2 rounded-xl border border-amber-400/30 bg-amber-400/10 p-3 text-xs ${tone}`}>
      <Info className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{text ?? 'Figures are modelled estimates on synthetic demo data. Framework mapping is an assessment aid, not a claim of certification or compliance.'}</span>
    </div>
  )
}

/** Collapsible "how this number is computed" panel — explainability everywhere. */
export function Explain({ title = 'How this is calculated', children }: { title?: string; children: ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-3 rounded-xl border border-hairline bg-elevated">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-body hover:text-accent"
      >
        <span className="inline-flex items-center gap-1.5"><Info className="h-3.5 w-3.5" /> {title}</span>
        <ChevronDown className={`h-4 w-4 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="border-t border-hairline px-3 py-2.5 text-xs leading-relaxed text-muted">{children}</div>}
    </div>
  )
}

export { inr, pct }
