// Investment Optimizer — real budget-constrained 0/1 knapsack. Results genuinely
// change with the budget; the efficient-frontier curve plots loss-reduction vs spend.

import { useCallback, useEffect, useState } from 'react'
import { SlidersHorizontal, Play } from 'lucide-react'
import { post } from '../api/client'
import type { OptimizeResult, OptimizeSelected } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, Disclaimer, StatCard, Explain, ProgressBar,
} from '../components/ui'
import { DataTable, Column } from '../components/DataTable'
import { LineCard } from '../components/charts'
import { inr, pctRaw, pct } from '../lib/format'

const PRESETS = [5_000_000, 10_000_000, 20_000_000, 50_000_000]

export default function Optimizer() {
  const [budget, setBudget] = useState(20_000_000)
  const [res, setRes] = useState<OptimizeResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (b: number) => {
    setLoading(true); setError(null)
    try {
      setRes(await post<OptimizeResult>('/api/optimizer/run', { budget_inr: b }))
    } catch (e: any) {
      setError(e?.message ?? 'Optimization failed')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { run(20_000_000) }, [run])

  const selCols: Column<OptimizeSelected>[] = [
    { key: 'name', header: 'Selected investment', render: s => (
      <div><div className="font-medium text-fg">{s.name}</div><div className="text-xs text-subtle">{s.category} · {s.action}</div></div>
    ) },
    { key: 'cost', header: 'Cost', align: 'right', sortValue: s => s.cost_inr, render: s => <Money v={s.cost_inr} /> },
    { key: 'red', header: 'Loss reduction', align: 'right', sortValue: s => s.marginal_ale_reduction_inr, render: s => <Money v={s.marginal_ale_reduction_inr} className="text-risk-low" /> },
    { key: 'eff', header: 'Efficiency', align: 'right', sortValue: s => s.efficiency, render: s => `${s.efficiency.toFixed(2)}×` },
  ]

  const curve = (res?.curve ?? []).map(p => ({ cost: p.cumulative_cost_inr, reduction: p.cumulative_ale_reduction_inr, label: p.label }))

  return (
    <div className="space-y-6">
      <SectionTitle title="Investment Optimizer" subtitle="Maximise expected-loss reduction within a fixed budget (0/1 knapsack)" />

      <CardPad>
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-[220px] flex-1">
            <label className="stat-label">Security budget (INR)</label>
            <div className="mt-2 flex items-center gap-3">
              <input type="range" min={1_000_000} max={100_000_000} step={1_000_000} value={budget}
                onChange={e => setBudget(Number(e.target.value))} className="w-full accent-brand-500" />
              <span className="w-24 text-right font-semibold text-fg">{inr(budget)}</span>
            </div>
            <div className="mt-2 flex gap-1.5">
              {PRESETS.map(p => (
                <button key={p} onClick={() => { setBudget(p); run(p) }} className={`chip ${budget === p ? 'bg-brand-600/30 text-brand-100 ring-1 ring-brand-500/40' : 'bg-hover/10 text-body'}`}>{inr(p)}</button>
              ))}
            </div>
          </div>
          <button className="btn-primary" onClick={() => run(budget)} disabled={loading}>
            <Play className="h-4 w-4" /> {loading ? 'Optimizing…' : 'Optimize'}
          </button>
        </div>
      </CardPad>

      {loading && !res ? <Loading label="Solving knapsack…" /> : error ? <ErrorState message={error} onRetry={() => run(budget)} /> : res && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Selected" value={`${res.selected_count} controls`} icon={<SlidersHorizontal className="h-4 w-4" />} />
            <StatCard label="Spend / budget" value={<Money v={res.total_cost_inr} />} sub={<>{pct(res.budget_utilization)} of {res.budget_display}</>} />
            <StatCard label="Joint loss reduction" value={res.joint_ale_reduction_display} sub={pctRaw(res.joint_ale_reduction_pct)} accent="text-risk-low" />
            <StatCard label="Portfolio ROSI" value={pctRaw(res.portfolio_rosi_percent)} accent="text-brand-300" />
          </div>

          <div className="grid gap-4 lg:grid-cols-5">
            <CardPad className="lg:col-span-3">
              <SectionTitle title="Selected portfolio" subtitle="Optimal set within budget" />
              <DataTable columns={selCols} rows={res.selected} initialSort={{ key: 'red', dir: 'desc' }} empty="No investments fit this budget." />
              <div className="mt-3"><ProgressBar value={res.budget_utilization} /></div>
              <Explain title="How the optimizer decides">
                A 0/1 knapsack maximises total expected-annual-loss reduction subject to Σ cost ≤ budget. Marginal reductions are
                computed against the current baseline, so raising the budget admits additional controls and the selected set changes.
                Joint reduction re-runs the full risk model with all selected controls applied together (it is not a naïve sum), which
                is why joint reduction can differ from the marginal sum ({inr(res.marginal_sum_ale_reduction_inr)}).
              </Explain>
            </CardPad>
            <CardPad className="lg:col-span-2">
              <SectionTitle title="Investment vs risk-reduction" subtitle="Efficient frontier" />
              {curve.length > 1
                ? <LineCard data={curve} xKey="cost" series={[{ key: 'reduction', label: 'Cumulative loss reduction', color: '#34d399' }]} area />
                : <div className="py-12 text-center text-sm text-subtle">Curve appears once investments are selected.</div>}
            </CardPad>
          </div>

          {res.not_selected?.length > 0 && (
            <CardPad>
              <SectionTitle title="Not selected" subtitle="Deferred at this budget — raise the budget to include them" />
              <DataTable columns={selCols} rows={res.not_selected} initialSort={{ key: 'eff', dir: 'desc' }} dense />
            </CardPad>
          )}
        </>
      )}

      <Disclaimer text={res?.note} />
    </div>
  )
}
