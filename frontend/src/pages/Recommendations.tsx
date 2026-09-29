// Recommendations — prioritized mitigations with cost-benefit (ROSI). Each card
// exposes the rationale: why, the current control state, and the exact formula.

import { useApi } from '../lib/useApi'
import type { Recommendation } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, Disclaimer, StatCard, Explain, ProgressBar,
} from '../components/ui'
import { pctRaw, pct } from '../lib/format'
import { TrendingUp, ArrowDownRight } from 'lucide-react'

function priorityChip(p: string) {
  const s = p.toLowerCase()
  if (s.includes('critical') || s.includes('immediate')) return 'bg-risk-critical/15 text-risk-critical ring-1 ring-risk-critical/30'
  if (s.includes('high')) return 'bg-risk-high/15 text-risk-high ring-1 ring-risk-high/30'
  if (s.includes('med')) return 'bg-risk-medium/15 text-risk-medium ring-1 ring-risk-medium/30'
  return 'bg-risk-low/15 text-risk-low ring-1 ring-risk-low/30'
}

export default function Recommendations() {
  const { data, loading, error, reload } = useApi<{ count: number; recommendations: Recommendation[]; summary: any; disclaimer: string }>('/api/recommendations', { refreshOnTelemetry: true })
  if (loading) return <Loading label="Generating recommendations…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const recs = data.recommendations
  const totalReduction = recs.reduce((s, r) => s + r.expected_ale_reduction_inr, 0)
  const totalCost = recs.reduce((s, r) => s + r.cost_inr, 0)

  return (
    <div className="space-y-6">
      <SectionTitle title="Mitigation Recommendations" subtitle="Ranked by risk-reduction return on security investment (ROSI)" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Recommendations" value={data.count} />
        <StatCard label="Total annual-loss reduction" value={<Money v={totalReduction} />} accent="text-risk-low" icon={<ArrowDownRight className="h-4 w-4" />} />
        <StatCard label="Total investment" value={<Money v={totalCost} />} />
        <StatCard label="Blended ROSI" value={pctRaw(totalCost > 0 ? (totalReduction - totalCost) / totalCost * 100 : 0)} accent="text-brand-300" icon={<TrendingUp className="h-4 w-4" />} />
      </div>

      <div className="space-y-4">
        {recs.map(r => (
          <div key={r.key} className="card card-pad">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Chip className={priorityChip(r.priority)}>{r.priority}</Chip>
                  <span className="text-xs text-subtle">{r.category} · {r.effort} effort</span>
                </div>
                <h3 className="mt-1.5 text-base font-semibold text-fg">{r.title}</h3>
                <p className="mt-0.5 text-sm text-muted">{r.action}</p>
              </div>
              <div className="flex shrink-0 gap-4 text-right">
                <div><div className="stat-label">Investment</div><div className="mt-0.5 font-bold text-fg">{r.cost_display ?? '—'}</div></div>
                <div><div className="stat-label">Loss reduction</div><div className="mt-0.5 font-bold text-risk-low">{r.expected_ale_reduction_display ?? '—'}</div></div>
                <div><div className="stat-label">ROSI</div><div className="mt-0.5 font-bold text-brand-300">{pctRaw(r.rosi_percent)}</div></div>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-3">
              <span className="text-xs text-subtle">Risk reduction</span>
              <div className="max-w-xs flex-1"><ProgressBar value={r.expected_risk_reduction} color="bg-risk-low" /></div>
              <span className="text-xs text-muted">{pct(r.expected_risk_reduction)}</span>
            </div>

            <Explain title="Why this is recommended">
              <p className="mb-2">{r.rationale?.why}</p>
              {r.rationale?.formula && <div className="mb-2 rounded bg-elevated/60 p-2 font-mono text-[11px] text-muted">{r.rationale.formula}</div>}
              {r.affected_assets?.length > 0 && (
                <div>
                  <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-subtle">Affected assets ({r.affected_assets.length})</div>
                  <div className="flex flex-wrap gap-1.5">
                    {r.affected_assets.slice(0, 8).map(a => (
                      <span key={a.asset_id} className="chip bg-hover/10 text-body">{a.name} · <Money v={a.ale_reduction_inr} /></span>
                    ))}
                  </div>
                </div>
              )}
              {r.rationale?.disclaimer && <p className="mt-2 text-[11px] text-amber-200/70">{r.rationale.disclaimer}</p>}
            </Explain>
          </div>
        ))}
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
