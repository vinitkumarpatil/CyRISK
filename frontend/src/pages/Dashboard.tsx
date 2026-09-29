// Executive dashboard — the headline monetary risk view. All figures come from
// GET /api/dashboard (the backend risk engine); nothing is computed client-side.

import { Link } from 'react-router-dom'
import { Activity, ShieldAlert, Layers, ArrowRight, Cpu, Server } from 'lucide-react'
import { useApi } from '../lib/useApi'
import type { Dashboard as Dash } from '../api/types'
import {
  Loading, ErrorState, StatCard, CardPad, SectionTitle, RiskBadge, Money,
  Explain, Disclaimer, ProgressBar, Chip,
} from '../components/ui'
import { BarCard, DonutCard, LineCard } from '../components/charts'
import { DataTable, Column } from '../components/DataTable'
import { pctRaw, pct, bandHex, inr } from '../lib/format'
import type { Contributor } from '../api/types'

export default function Dashboard() {
  const { data, loading, error, reload } = useApi<Dash>('/api/dashboard', { refreshOnTelemetry: true })
  if (loading) return <Loading label="Computing enterprise risk…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const e = data.enterprise
  const bd = e.risk_score_breakdown

  // New / empty tenant: no assets yet → show onboarding empty-state instead of
  // a wall of zeros. Data appears once the company adds assets & findings.
  if (e.asset_count === 0) {
    return (
      <div className="space-y-6">
        <CardPad>
          <div className="flex flex-col items-center py-12 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand-gradient shadow-glow">
              <Layers className="h-7 w-7 text-white" />
            </div>
            <h2 className="mt-4 text-xl font-bold text-fg">No assets have been added yet</h2>
            <p className="mt-2 max-w-md text-sm text-muted">
              Your organization’s risk dashboard is empty. Add assets, vulnerabilities and
              controls to begin quantifying cyber risk in ₹. Every figure here is computed by
              the risk engine from your own data — nothing is pre-filled.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              <Link to="/assets" className="btn-primary text-sm"><Server className="h-4 w-4" /> Add assets</Link>
              <Link to="/telemetry" className="btn-ghost text-sm">Import from data sources</Link>
            </div>
          </div>
        </CardPad>
        <Disclaimer text={data.disclaimer} />
      </div>
    )
  }

  const contribCols: Column<Contributor>[] = [
    { key: 'label', header: 'Risk driver', render: r => (
      <div><div className="font-medium text-fg">{r.label}</div>
        <div className="text-xs text-subtle">{r.category} · {r.severity}</div></div>
    ) },
    { key: 'ale', header: 'Annual loss', align: 'right', sortValue: r => r.ale_inr, render: r => <Money v={r.ale_inr} className="font-semibold text-risk-high" /> },
    { key: 'share', header: 'Share', align: 'right', sortValue: r => r.share, render: r => pct(r.share) },
    { key: 'fix', header: 'If mitigated', align: 'right', sortValue: r => r.expected_reduction_inr, render: r => <Money v={r.expected_reduction_inr} className="text-risk-low" /> },
  ]

  const buData = data.by_business_unit.map(b => ({ name: b.business_unit, value: b.ale_inr }))
  const catData = data.by_category.map(c => ({ name: c.category, value: c.ale_inr }))
  const trendPoints = (data.trend?.points ?? []).map((p: any, i: number) => ({
    t: p.label ?? p.captured_at ?? `T${i + 1}`,
    ale: p.total_ale_inr ?? p.ale_inr ?? p.ale ?? 0,
    score: p.risk_score ?? p.score ?? null,
  }))

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-fg">Enterprise Risk Overview</h1>
          <p className="mt-1 text-sm text-muted">Continuous quantification of cyber risk in ₹ — every figure is computed by the risk engine.</p>
        </div>
        <RiskBadge band={e.risk_band} />
      </div>

      {/* Headline KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="card card-pad">
          <div className="flex items-start justify-between">
            <div className="stat-label">Enterprise Risk Score</div>
            <Activity className="h-4 w-4 text-subtle" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight" style={{ color: bandHex(e.risk_band) }}>{e.risk_score}</span>
            <span className="text-sm text-subtle">/100</span>
          </div>
          <div className="mt-2"><RiskBadge band={e.risk_band} /></div>
        </div>
        <StatCard label="Expected Annual Loss" value={<Money v={e.total_ale_inr} />} sub="Σ ALE across findings" accent="text-risk-high" icon={<ShieldAlert className="h-4 w-4" />} />
        <StatCard label="Value-at-Risk (95%)" value={<Money v={e.var95_inr} />} sub={<>99%: <Money v={e.var99_inr} /></>} accent="text-risk-medium" />
        <StatCard label="Total Exposure" value={<Money v={e.total_exposure_inr} />} sub={`${e.asset_count} assets · ${e.open_vulns} open vulns`} icon={<Layers className="h-4 w-4" />} />
      </div>

      {/* Risk score composition */}
      <CardPad>
        <SectionTitle title="Risk score composition" subtitle="Weighted blend of expected loss, control gaps and critical exposure" />
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { k: 'Expected loss', v: bd.ale_component, w: bd.weights.ale, c: 'bg-risk-high' },
            { k: 'Control gaps', v: bd.control_component, w: bd.weights.control, c: 'bg-risk-medium' },
            { k: 'Critical vulns', v: bd.critical_vuln_component, w: bd.weights.critical_vulns, c: 'bg-brand-500' },
          ].map(x => (
            <div key={x.k} className="rounded-xl border border-hairline bg-elevated/40 p-3">
              <div className="flex items-center justify-between text-sm"><span className="text-body">{x.k}</span><span className="font-semibold text-fg">{x.v.toFixed(1)}</span></div>
              <div className="mt-2"><ProgressBar value={x.v / 100} color={x.c} /></div>
              <div className="mt-1 text-[11px] text-subtle">weight {pct(x.w, 0)}</div>
            </div>
          ))}
        </div>
        <Explain>
          The score = <span className="font-mono">ale_component×{pct(bd.weights.ale, 0)} + control_component×{pct(bd.weights.control, 0)} + critical_vuln_component×{pct(bd.weights.critical_vulns, 0)}</span>.
          Each component is normalised to 0–100. Average control effectiveness is {pct(e.avg_control_effectiveness)}, mean likelihood {pct(e.likelihood_avg)}.
        </Explain>
      </CardPad>

      {/* Top contributors */}
      <CardPad>
        <SectionTitle title="Top risk contributors" subtitle="Findings ranked by contribution to expected annual loss"
          right={<Link to="/recommendations" className="link-muted inline-flex items-center gap-1 text-sm">Mitigations <ArrowRight className="h-3.5 w-3.5" /></Link>} />
        <DataTable columns={contribCols} rows={data.top_contributors} initialSort={{ key: 'ale', dir: 'desc' }} />
      </CardPad>

      {/* Distribution charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <CardPad>
          <SectionTitle title="Annual loss by business unit" />
          <DonutCard data={buData} nameKey="name" valueKey="value" />
        </CardPad>
        <CardPad>
          <SectionTitle title="Annual loss by category" />
          <BarCard data={catData} xKey="name" yKey="value" color="#f43f5e" />
        </CardPad>
      </div>

      {/* Weakest controls + framework posture */}
      <div className="grid gap-4 lg:grid-cols-2">
        <CardPad>
          <SectionTitle title="Weakest controls" subtitle="Lowest assessed effectiveness"
            right={<Link to="/controls" className="link-muted text-sm">All controls</Link>} />
          <div className="space-y-3">
            {data.weakest_controls.map(c => (
              <div key={c.key}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-body">{c.name}</span>
                  <span className="text-muted">{pct(c.effectiveness)} · <Chip className="bg-hover/10 text-body">{c.rating}</Chip></span>
                </div>
                <div className="mt-1.5"><ProgressBar value={c.effectiveness} color={c.effectiveness < 0.5 ? 'bg-risk-high' : 'bg-risk-medium'} /></div>
              </div>
            ))}
          </div>
        </CardPad>
        <CardPad>
          <SectionTitle title="Framework posture" subtitle="Assessment index — an internal aid, not certification"
            right={<Link to="/frameworks" className="link-muted text-sm">Detail</Link>} />
          <div className="space-y-3">
            {data.framework_coverage.map(f => (
              <div key={f.key}>
                <div className="flex items-center justify-between text-sm"><span className="text-body">{f.name}</span><span className="text-muted">{pctRaw(f.assessment_index)}</span></div>
                <div className="mt-1.5"><ProgressBar value={f.assessment_index / 100} color="bg-brand-500" /></div>
              </div>
            ))}
          </div>
        </CardPad>
      </div>

      {/* ML + trend */}
      <div className="grid gap-4 lg:grid-cols-2">
        <CardPad>
          <SectionTitle title="Incident likelihood model" subtitle="scikit-learn — hybrid with actuarial formulas"
            right={<Link to="/model" className="link-muted inline-flex items-center gap-1 text-sm"><Cpu className="h-3.5 w-3.5" /> Model card</Link>} />
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(data.ml_model.metrics).slice(0, 3).map(([k, v]) => (
              <div key={k} className="rounded-xl border border-hairline bg-elevated/40 p-3 text-center">
                <div className="text-lg font-bold text-fg">{typeof v === 'number' ? (v as number).toFixed(3) : String(v)}</div>
                <div className="text-[11px] uppercase tracking-wide text-subtle">{k.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 space-y-2">
            {Object.entries(data.ml_model.importances).slice(0, 5).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between text-xs text-muted"><span>{k.replace(/_/g, ' ')}</span><span>{pct(v as number)}</span></div>
                <ProgressBar value={v as number} />
              </div>
            ))}
          </div>
        </CardPad>
        <CardPad>
          <SectionTitle title="Risk trend" subtitle={data.trend?.note ?? 'Recent snapshots — simulate telemetry to add points'} />
          {trendPoints.length > 1
            ? <LineCard data={trendPoints} xKey="t" series={[{ key: 'ale', label: 'Annual loss', color: '#f43f5e' }]} area />
            : <div className="py-12 text-center text-sm text-subtle">Only one snapshot so far. Use “Simulate Telemetry” to generate a trend.</div>}
        </CardPad>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
