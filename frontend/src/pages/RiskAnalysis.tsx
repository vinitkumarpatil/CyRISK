// Risk Analysis — the explainable financial model. Every finding exposes its
// full SLE → ARO → ALE derivation and the Monte-Carlo VaR is broken out.

import { useState, ReactNode } from 'react'
import { useApi } from '../lib/useApi'
import type { RiskResult, Finding } from '../api/types'
import {
  Loading, ErrorState, StatCard, CardPad, SectionTitle, RiskBadge, Money, Explain, Disclaimer,
} from '../components/ui'
import { DataTable, Column } from '../components/DataTable'
import { Modal } from '../components/Modal'
import { inr, pct, num } from '../lib/format'

export default function RiskAnalysis() {
  const { data, loading, error, reload } = useApi<RiskResult>('/api/risk', { refreshOnTelemetry: true })
  const [sel, setSel] = useState<Finding | null>(null)
  if (loading) return <Loading label="Running risk model…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const e = data.enterprise
  const v = e.var_detail
  const cols: Column<Finding>[] = [
    { key: 'title', header: 'Finding', render: f => (
      <div><div className="font-medium text-fg">{f.title}</div>
        <div className="text-xs text-subtle">{f.asset_name} · {f.cve_id || f.category}</div></div>
    ) },
    { key: 'sev', header: 'Severity', render: f => <RiskBadge band={f.severity} /> },
    { key: 'sle', header: 'SLE', align: 'right', sortValue: f => f.sle_inr, render: f => <Money v={f.sle_inr} /> },
    { key: 'aro', header: 'ARO', align: 'right', sortValue: f => f.aro, render: f => f.aro.toFixed(3) },
    { key: 'ale', header: 'ALE', align: 'right', sortValue: f => f.ale_inr, render: f => <Money v={f.ale_inr} className="font-semibold text-risk-high" /> },
    { key: 'lk', header: 'Likelihood', align: 'right', sortValue: f => f.likelihood, render: f => pct(f.likelihood) },
  ]

  return (
    <div className="space-y-6">
      <SectionTitle title="Risk Quantification" subtitle="Single Loss Expectancy × Annualized Rate of Occurrence = Annual Loss, with Monte-Carlo Value-at-Risk" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Expected Annual Loss" value={<Money v={e.total_ale_inr} />} accent="text-risk-high" />
        <StatCard label="VaR 95%" value={<Money v={e.var95_inr} />} sub="1-in-20 bad year" accent="text-risk-medium" />
        <StatCard label="VaR 99%" value={<Money v={e.var99_inr} />} sub="1-in-100 bad year" accent="text-risk-critical" />
        <StatCard label="Open findings" value={num(data.findings.length)} sub={`${e.critical_vulns} critical`} />
      </div>

      <CardPad>
        <SectionTitle title="Loss distribution (Monte-Carlo)" subtitle={`${num(v.simulations)} simulations · Poisson frequency × lognormal severity`} />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Mean loss" value={<Money v={v.mean_inr} />} />
          <StatCard label="Median (P50)" value={<Money v={v.p50_inr} />} />
          <StatCard label="P95" value={<Money v={v.var95_inr} />} accent="text-risk-medium" />
          <StatCard label="P99" value={<Money v={v.var99_inr} />} accent="text-risk-critical" />
        </div>
        <Explain>
          Each simulation draws an annual event count from a Poisson process (λ = Σ finding frequencies) and a severity per event
          from a lognormal fitted to per-finding SLE. Value-at-Risk is the 95th/99th percentile of the resulting annual-loss
          distribution — the loss you would not expect to exceed in 19-of-20 (95%) or 99-of-100 (99%) years.
        </Explain>
      </CardPad>

      <CardPad>
        <SectionTitle title="Findings" subtitle="Click any row for the full derivation" />
        <DataTable columns={cols} rows={data.findings} initialSort={{ key: 'ale', dir: 'desc' }} onRowClick={setSel} />
      </CardPad>

      <Disclaimer text="Figures are modelled estimates on synthetic demo data using standard actuarial risk formulas (SLE/ARO/ALE) and Monte-Carlo simulation." />

      <FindingModal finding={sel} onClose={() => setSel(null)} />
    </div>
  )
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-hairline py-1.5 text-sm last:border-0">
      <span className="text-muted">{label}</span>
      <span className="font-medium text-fg">{value}</span>
    </div>
  )
}

function FindingModal({ finding, onClose }: { finding: Finding | null; onClose: () => void }) {
  if (!finding) return null
  const f = finding
  const imp = f.impact, fr = f.frequency
  return (
    <Modal open={!!finding} onClose={onClose} wide title={<span>{f.title} <span className="text-sm font-normal text-subtle">· {f.asset_name}</span></span>}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-hairline bg-elevated/40 p-3">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Impact → Single Loss Expectancy</div>
          {Object.entries(imp.components).map(([k, val]) => (
            <Row key={k} label={k.replace(/_/g, ' ')} value={<Money v={val as number} />} />
          ))}
          <Row label="Exposure factor" value={imp.exposure_factor.toFixed(2)} />
          <Row label="Severity factor" value={imp.severity_factor.toFixed(2)} />
          <div className="mt-2 flex items-center justify-between rounded-lg bg-brand-600/15 px-2.5 py-2 text-sm">
            <span className="font-semibold text-brand-200">SLE</span><Money v={imp.sle_inr} className="font-bold text-brand-100" />
          </div>
        </div>
        <div className="rounded-xl border border-hairline bg-elevated/40 p-3">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Frequency → Annualized Rate</div>
          <Row label="Base rate" value={fr.base_rate.toFixed(3)} />
          <Row label="× Exposure" value={fr.exposure_multiplier.toFixed(2)} />
          <Row label="× Age" value={fr.age_multiplier.toFixed(2)} />
          <Row label="× Threat" value={fr.threat_multiplier.toFixed(2)} />
          <Row label="Raw λ" value={fr.raw_lambda.toFixed(3)} />
          <Row label="Control effectiveness" value={pct(fr.control_effectiveness)} />
          <Row label="After controls" value={fr.after_controls.toFixed(3)} />
          <Row label="ML probability" value={pct(fr.ml_probability)} />
          <Row label="× ML multiplier" value={fr.ml_multiplier.toFixed(2)} />
          <div className="mt-2 flex items-center justify-between rounded-lg bg-brand-600/15 px-2.5 py-2 text-sm">
            <span className="font-semibold text-brand-200">ARO</span><span className="font-bold text-brand-100">{fr.aro.toFixed(3)}</span>
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between rounded-xl border border-risk-high/30 bg-risk-high/10 px-4 py-3">
        <span className="text-sm font-semibold text-body">Annual Loss (ALE = SLE × ARO)</span>
        <Money v={f.ale_inr} className="text-xl font-bold text-risk-high" />
      </div>
      {f.formula && (
        <div className="mt-3 rounded-lg bg-elevated/60 p-3 font-mono text-xs leading-relaxed text-muted">{f.formula}</div>
      )}
      {f.controls_considered?.length > 0 && (
        <div className="mt-3">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Controls considered</div>
          <div className="flex flex-wrap gap-2">
            {f.controls_considered.map(c => (
              <span key={c.key} className="chip bg-hover/10 text-body">{c.key}: {pct(c.effectiveness)}</span>
            ))}
          </div>
        </div>
      )}
    </Modal>
  )
}
