// Data Sources — the demo connectors that feed telemetry, plus the continuous
// snapshot history. "Simulate Telemetry" ingests a new batch and re-scores risk.

import { useState } from 'react'
import { Radio, Zap, Activity, CheckCircle2, AlertCircle } from 'lucide-react'
import { useApi } from '../lib/useApi'
import { post } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import {
  Loading, ErrorState, CardPad, SectionTitle, Chip, Disclaimer, StatCard,
} from '../components/ui'
import { LineCard } from '../components/charts'
import { shortDate, num, inr } from '../lib/format'

interface Source {
  id: number; source_type: string; name: string; vendor: string; status: string
  record_count: number; health: string; last_sync: string; description: string
}

function healthChip(h: string) {
  const s = (h || '').toLowerCase()
  if (s.includes('healthy') || s.includes('ok') || s.includes('connected')) return 'bg-risk-low/15 text-risk-low ring-1 ring-risk-low/30'
  if (s.includes('degraded') || s.includes('warn')) return 'bg-risk-medium/15 text-risk-medium ring-1 ring-risk-medium/30'
  if (s.includes('down') || s.includes('error') || s.includes('fail')) return 'bg-risk-high/15 text-risk-high ring-1 ring-risk-high/30'
  return 'bg-hover/10 text-body ring-1 ring-white/10'
}

export default function DataSources() {
  const { user } = useAuth()
  const canRun = user?.role === 'ciso' || user?.role === 'analyst'
  const tele = useApi<{ count: number; sources: Source[]; note?: string }>('/api/telemetry', { refreshOnTelemetry: true })
  const snaps = useApi<{ snapshots: any[] }>('/api/risk/snapshots', { refreshOnTelemetry: true })
  const [busy, setBusy] = useState(false)
  const [flash, setFlash] = useState<string | null>(null)

  async function simulate() {
    setBusy(true); setFlash(null)
    try {
      const r = await post('/api/demo/simulate-telemetry')
      setFlash(`Ingested batch → risk ${r.risk_score} (${r.risk_band}), ALE ${inr(r.total_ale_inr)}.`)
      window.dispatchEvent(new CustomEvent('risk-refresh'))
    } catch (e: any) { setFlash(e?.message ?? 'Failed') } finally { setBusy(false) }
  }

  if (tele.loading) return <Loading label="Loading data sources…" />
  if (tele.error || !tele.data) return <ErrorState message={tele.error ?? 'No data'} onRetry={tele.reload} />

  const points = (snaps.data?.snapshots ?? []).map((s: any, i: number) => ({
    t: shortDate(s.captured_at) || `#${i + 1}`,
    ale: s.total_ale_inr ?? s.ale_inr ?? 0,
    score: s.risk_score ?? null,
  }))

  return (
    <div className="space-y-6">
      <SectionTitle title="Data Sources & Continuous Monitoring" subtitle="Security telemetry connectors feeding the risk engine"
        right={canRun && <button className="btn-primary !py-1.5" onClick={simulate} disabled={busy}><Zap className="h-4 w-4" />{busy ? 'Ingesting…' : 'Simulate Telemetry'}</button>} />

      {flash && <div className="rounded-xl border border-brand-500/20 bg-brand-600/10 px-4 py-2.5 text-sm text-brand-100">{flash}</div>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Connectors" value={num(tele.data.count)} icon={<Radio className="h-4 w-4" />} />
        <StatCard label="Healthy" value={num(tele.data.sources.filter(s => healthChip(s.health).includes('low')).length)} accent="text-risk-low" />
        <StatCard label="Total records" value={num(tele.data.sources.reduce((s, x) => s + (x.record_count || 0), 0))} />
        <StatCard label="Snapshots" value={num(points.length)} icon={<Activity className="h-4 w-4" />} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tele.data.sources.map(s => (
          <div key={s.id} className="card card-pad">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-semibold text-fg">{s.name}</div>
                <div className="text-xs text-subtle">{s.vendor} · {s.source_type}</div>
              </div>
              <Chip className={healthChip(s.health)}>
                {healthChip(s.health).includes('low') ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />} {s.health}
              </Chip>
            </div>
            <p className="mt-2 text-xs text-muted">{s.description}</p>
            <div className="mt-3 flex items-center justify-between border-t border-hairline pt-2 text-xs text-subtle">
              <span>{num(s.record_count)} records</span>
              <span>synced {shortDate(s.last_sync)}</span>
            </div>
          </div>
        ))}
      </div>

      <CardPad>
        <SectionTitle title="Risk trend across snapshots" subtitle="Each telemetry ingestion writes an immutable snapshot" />
        {points.length > 1
          ? <LineCard data={points} xKey="t" series={[{ key: 'ale', label: 'Annual loss', color: '#f43f5e' }]} area />
          : <div className="py-10 text-center text-sm text-subtle">Simulate telemetry a few times to build the trend.</div>}
      </CardPad>

      <Disclaimer text={tele.data.note ?? 'Connectors and telemetry are synthetic demo sources. No live systems are contacted.'} />
    </div>
  )
}
