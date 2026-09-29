// What-if Scenarios — genuinely recomputes the risk model with selected
// mitigations applied to a cloned state. Before/after and deltas are all live.

import { useEffect, useMemo, useState } from 'react'
import { GitBranch, Play, Check } from 'lucide-react'
import { get, post } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { InvestmentOption, ScenarioResult } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, Disclaimer, StatCard, Explain,
} from '../components/ui'
import { inr, pctRaw, pct } from '../lib/format'

export default function Scenarios() {
  const { user } = useAuth()
  const canRun = user?.role === 'ciso' || user?.role === 'analyst'
  const [options, setOptions] = useState<InvestmentOption[]>([])
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const [res, setRes] = useState<ScenarioResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    get('/api/investments')
      .then(d => setOptions(d.options ?? []))
      .catch(e => setError(e?.message ?? 'Failed to load options'))
      .finally(() => setLoading(false))
  }, [])

  const pickedCost = useMemo(
    () => options.filter(o => picked.has(o.key)).reduce((s, o) => s + o.cost_inr, 0),
    [options, picked],
  )

  function toggle(key: string) {
    setPicked(p => { const n = new Set(p); n.has(key) ? n.delete(key) : n.add(key); return n })
  }

  async function run() {
    if (!picked.size) return
    setRunning(true); setError(null)
    try {
      const r = await post<ScenarioResult>('/api/scenarios/investment', {
        option_keys: [...picked], save: false, name: 'What-if analysis',
      })
      setRes(r)
    } catch (e: any) {
      setError(e?.message ?? 'Simulation failed')
    } finally { setRunning(false) }
  }

  if (loading) return <Loading label="Loading investment options…" />
  if (error && !options.length) return <ErrorState message={error} />

  const before = res?.before, after = res?.after, d = res?.delta
  const g = (o: any, k: string) => (o?.[k] ?? o?.[`${k}_inr`] ?? 0) as number

  return (
    <div className="space-y-6">
      <SectionTitle title="What-if Scenario Simulator" subtitle="Select mitigations, then recompute the full risk model on a cloned state" />

      {!canRun && (
        <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200/80">
          Your role (<b>{user?.role}</b>) has read-only access. Scenario simulation requires the CISO or analyst role.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-5">
        <CardPad className="lg:col-span-2">
          <SectionTitle title="Mitigations" subtitle={`${picked.size} selected · ${inr(pickedCost)}`} />
          <div className="max-h-[460px] space-y-2 overflow-y-auto pr-1">
            {options.map(o => {
              const on = picked.has(o.key)
              return (
                <button key={o.key} onClick={() => toggle(o.key)} disabled={!canRun}
                  className={`flex w-full items-start gap-3 rounded-xl border p-3 text-left transition disabled:opacity-60 ${on ? 'border-brand-500/50 bg-brand-600/15' : 'border-hairline-strong bg-hover/[0.02] hover:bg-hover/5'}`}>
                  <span className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded border ${on ? 'border-brand-400 bg-brand-500 text-white' : 'border-hairline-strong'}`}>{on && <Check className="h-3 w-3" />}</span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium text-fg">{o.name}</span>
                    <span className="block text-xs text-subtle">{o.category} · {o.effort}</span>
                    <span className="mt-1 flex gap-3 text-xs"><span className="text-muted">{o.cost_display}</span><span className="text-risk-low">−{o.marginal_ale_reduction_display}</span><span className="text-brand-300">{pctRaw(o.rosi_percent)} ROSI</span></span>
                  </span>
                </button>
              )
            })}
          </div>
          <button className="btn-primary mt-3 w-full" onClick={run} disabled={!canRun || !picked.size || running}>
            <Play className="h-4 w-4" /> {running ? 'Recomputing…' : 'Run scenario'}
          </button>
        </CardPad>

        <div className="lg:col-span-3">
          {!res ? (
            <CardPad className="flex h-full flex-col items-center justify-center py-16 text-center text-subtle">
              <GitBranch className="mb-3 h-10 w-10 text-subtle" />
              Select one or more mitigations and run the scenario to see the recomputed risk posture.
            </CardPad>
          ) : (
            <div className="space-y-4">
              {error && <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{error}</div>}
              <div className="grid grid-cols-2 gap-4">
                <StatCard label="Annual loss reduction" value={<Money v={d?.ale_reduction_inr} />} sub={pctRaw(d?.ale_reduction_pct ?? 0)} accent="text-risk-low" />
                <StatCard label="Scenario cost" value={<Money v={res.cost_inr} />} sub={<>ROSI {pctRaw(res.rosi_percent)}</>} accent="text-brand-300" />
                <StatCard label="VaR 95% reduction" value={<Money v={d?.var95_reduction_inr} />} accent="text-risk-medium" />
                <StatCard label="Risk score change" value={(d?.risk_score_delta ?? 0).toFixed(1)} sub={`control eff ${d && d.control_eff_delta >= 0 ? '+' : ''}${pct(d?.control_eff_delta ?? 0)}`} />
              </div>
              <CardPad>
                <SectionTitle title="Before vs after" />
                <div className="space-y-2">
                  {[
                    { k: 'Expected annual loss', b: g(before, 'total_ale'), a: g(after, 'total_ale') },
                    { k: 'Total exposure', b: g(before, 'total_exposure'), a: g(after, 'total_exposure') },
                    { k: 'VaR 95%', b: g(before, 'var95'), a: g(after, 'var95') },
                  ].map(row => (
                    <div key={row.k} className="grid grid-cols-3 items-center gap-2 border-b border-hairline py-2 text-sm last:border-0">
                      <span className="text-muted">{row.k}</span>
                      <span className="text-right text-muted line-through">{inr(row.b)}</span>
                      <span className="text-right font-semibold text-risk-low">{inr(row.a)}</span>
                    </div>
                  ))}
                </div>
                <Explain title="How the scenario is computed">
                  Selected mitigations are applied to a deep-cloned copy of the current risk state (the live data is never modified),
                  then the entire engine re-runs — control effectiveness, per-finding likelihood, ALE and Monte-Carlo VaR are all
                  recalculated. Deltas compare the recomputed posture to the current baseline. ROSI = (loss reduction − cost) / cost.
                </Explain>
              </CardPad>
            </div>
          )}
        </div>
      </div>

      <Disclaimer />
    </div>
  )
}
