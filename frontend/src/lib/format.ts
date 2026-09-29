// Presentation helpers. Currency formatting mirrors the backend's fmt_inr so the
// UI and API agree (Indian crore/lakh convention).

export function inr(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return '₹0'
  const sign = amount < 0 ? '-' : ''
  const a = Math.abs(amount)
  if (a >= 1e7) return `${sign}₹${(a / 1e7).toFixed(2)} Cr`
  if (a >= 1e5) return `${sign}₹${(a / 1e5).toFixed(2)} L`
  if (a >= 1e3) return `${sign}₹${(a / 1e3).toFixed(1)} K`
  return `${sign}₹${a.toFixed(0)}`
}

/** x is a fraction in [0,1]. */
export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '0%'
  return `${(x * 100).toFixed(digits)}%`
}

/** x is already a percentage number (e.g. 42.5). */
export function pctRaw(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '0%'
  return `${x.toFixed(digits)}%`
}

export function num(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '0'
  return x.toLocaleString('en-IN')
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export type Band = 'Critical' | 'High' | 'Medium' | 'Low' | string

const BAND_STYLES: Record<string, string> = {
  Critical: 'bg-risk-critical/15 text-risk-critical ring-1 ring-risk-critical/30',
  High: 'bg-risk-high/15 text-risk-high ring-1 ring-risk-high/30',
  Medium: 'bg-risk-medium/15 text-risk-medium ring-1 ring-risk-medium/30',
  Low: 'bg-risk-low/15 text-risk-low ring-1 ring-risk-low/30',
}
export function bandChip(band: Band): string {
  return BAND_STYLES[band] ?? 'bg-hover/10 text-body ring-1 ring-hover/10'
}

const BAND_HEX: Record<string, string> = {
  Critical: '#f43f5e', High: '#fb923c', Medium: '#fbbf24', Low: '#34d399',
}
export function bandHex(band: Band): string {
  return BAND_HEX[band] ?? '#64748b'
}

/** Status vocabulary used by framework assessment + control ratings. */
export function statusChip(status: string): string {
  const s = status.toLowerCase()
  if (s.includes('covered') || s === 'strong') return 'bg-risk-low/15 text-risk-low ring-1 ring-risk-low/30'
  if (s.includes('partial') || s === 'moderate') return 'bg-risk-medium/15 text-risk-medium ring-1 ring-risk-medium/30'
  if (s.includes('gap') || s === 'weak') return 'bg-risk-high/15 text-risk-high ring-1 ring-risk-high/30'
  if (s.includes('review') || s.includes('critical')) return 'bg-risk-critical/15 text-risk-critical ring-1 ring-risk-critical/30'
  return 'bg-hover/10 text-body ring-1 ring-hover/10'
}

export const CHART_COLORS = ['#22d3ee', '#4f46e5', '#f43f5e', '#fb923c', '#fbbf24', '#34d399', '#a78bfa', '#38bdf8']
