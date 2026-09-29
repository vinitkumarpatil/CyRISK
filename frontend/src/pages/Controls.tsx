// Controls — transparent control effectiveness. Each control shows the inputs
// and sub-factors that produce its 0–1 effectiveness score (no black boxes).

import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { useApi } from '../lib/useApi'
import type { ControlOut } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Chip, ProgressBar, Disclaimer, StatCard, Explain,
} from '../components/ui'
import { Modal } from '../components/Modal'
import { pct, statusChip } from '../lib/format'

export default function Controls() {
  const { data, loading, error, reload } = useApi<{ count: number; avg_effectiveness: number; controls: ControlOut[] }>('/api/controls', { refreshOnTelemetry: true })
  const [sel, setSel] = useState<ControlOut | null>(null)
  if (loading) return <Loading label="Loading controls…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const sorted = [...data.controls].sort((a, b) => a.effectiveness - b.effectiveness)

  return (
    <div className="space-y-6">
      <SectionTitle title="Security Controls" subtitle="Assessed effectiveness feeds directly into likelihood reduction" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Controls" value={data.count} icon={<ShieldCheck className="h-4 w-4" />} />
        <StatCard label="Avg effectiveness" value={pct(data.avg_effectiveness)} accent={data.avg_effectiveness < 0.5 ? 'text-risk-high' : 'text-risk-low'} />
        <StatCard label="Weak (<50%)" value={sorted.filter(c => c.effectiveness < 0.5).length} accent="text-risk-high" />
        <StatCard label="Strong (≥75%)" value={sorted.filter(c => c.effectiveness >= 0.75).length} accent="text-risk-low" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sorted.map(c => (
          <button key={c.key} onClick={() => setSel(c)} className="card card-pad text-left transition hover:border-brand-500/30 hover:bg-hover/[0.03]">
            <div className="flex items-start justify-between">
              <div className="font-semibold text-fg">{c.name}</div>
              <Chip className={statusChip(c.rating)}>{c.rating}</Chip>
            </div>
            <div className="mt-0.5 text-xs text-subtle">{c.category}</div>
            <div className="mt-3 flex items-center justify-between text-sm"><span className="text-muted">Effectiveness</span><span className="font-semibold text-fg">{pct(c.effectiveness)}</span></div>
            <div className="mt-1.5"><ProgressBar value={c.effectiveness} color={c.effectiveness < 0.5 ? 'bg-risk-high' : c.effectiveness < 0.75 ? 'bg-risk-medium' : 'bg-risk-low'} /></div>
          </button>
        ))}
      </div>

      <Disclaimer />

      <Modal open={!!sel} onClose={() => setSel(null)} wide title={sel?.name ?? ''}>
        {sel && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Chip className={statusChip(sel.rating)}>{sel.rating}</Chip>
              <span className="text-sm text-muted">{sel.category}</span>
              <span className="ml-auto text-lg font-bold text-fg">{pct(sel.effectiveness)}</span>
            </div>
            <ProgressBar value={sel.effectiveness} color={sel.effectiveness < 0.5 ? 'bg-risk-high' : sel.effectiveness < 0.75 ? 'bg-risk-medium' : 'bg-risk-low'} />
            {sel.inputs && Object.keys(sel.inputs).length > 0 && (
              <div className="rounded-xl border border-hairline bg-elevated/40 p-3">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Inputs</div>
                <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                  {Object.entries(sel.inputs).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-hairline py-1 text-sm last:border-0">
                      <span className="text-muted">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-fg">{fmt(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {sel.detail && Object.keys(sel.detail).length > 0 && (
              <Explain title="Scoring detail">
                <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                  {Object.entries(sel.detail).map(([k, v]) => (
                    <div key={k} className="flex justify-between"><span className="text-subtle">{k.replace(/_/g, ' ')}</span><span className="text-body">{fmt(v)}</span></div>
                  ))}
                </div>
              </Explain>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

function fmt(v: any): string {
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(3)
  if (typeof v === 'boolean') return v ? 'yes' : 'no'
  return String(v)
}
