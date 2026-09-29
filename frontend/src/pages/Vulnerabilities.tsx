// Vulnerabilities — telemetry-sourced findings with CVSS, exploitability and the
// modelled annual loss each one contributes. Filterable by severity/status.

import { useMemo, useState } from 'react'
import { ShieldAlert, Bug, Wifi, Wrench } from 'lucide-react'
import { useApi } from '../lib/useApi'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, RiskBadge, Disclaimer, StatCard,
} from '../components/ui'
import { DataTable, Column } from '../components/DataTable'
import { num } from '../lib/format'

interface Vuln {
  id: number; cve_id: string; title: string; asset_id: number; asset_name: string
  cvss: number; severity: string; category: string; status: string
  exploit_available: boolean; internet_exposed: boolean; patch_available: boolean
  age_days: number; source: string; ale_inr: number; likelihood: number; sle_inr: number
}
interface VulnResp {
  count: number; by_severity: Record<string, number>; by_status: Record<string, number>; vulnerabilities: Vuln[]
}

const SEVS = ['Critical', 'High', 'Medium', 'Low']

export default function Vulnerabilities() {
  const { data, loading, error, reload } = useApi<VulnResp>('/api/vulnerabilities', { refreshOnTelemetry: true })
  const [sev, setSev] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  const rows = useMemo(() => {
    if (!data) return []
    return data.vulnerabilities.filter(v => (!sev || v.severity === sev) && (!status || v.status === status))
  }, [data, sev, status])

  if (loading) return <Loading label="Loading vulnerabilities…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const cols: Column<Vuln>[] = [
    { key: 'cve', header: 'Vulnerability', render: v => (
      <div><div className="font-medium text-fg">{v.title}</div>
        <div className="text-xs text-subtle">{v.cve_id || '—'} · {v.asset_name}</div></div>
    ) },
    { key: 'cvss', header: 'CVSS', align: 'right', sortValue: v => v.cvss, render: v => v.cvss.toFixed(1) },
    { key: 'sev', header: 'Severity', render: v => <RiskBadge band={v.severity} /> },
    { key: 'flags', header: 'Flags', render: v => (
      <div className="flex gap-1">
        {v.exploit_available && <span title="Exploit available" className="chip bg-risk-critical/15 text-risk-critical"><Bug className="h-3 w-3" /></span>}
        {v.internet_exposed && <span title="Internet exposed" className="chip bg-risk-high/15 text-risk-high"><Wifi className="h-3 w-3" /></span>}
        {v.patch_available && <span title="Patch available" className="chip bg-risk-low/15 text-risk-low"><Wrench className="h-3 w-3" /></span>}
      </div>
    ) },
    { key: 'status', header: 'Status', render: v => <Chip className="bg-hover/10 text-body capitalize">{v.status}</Chip> },
    { key: 'age', header: 'Age', align: 'right', sortValue: v => v.age_days, render: v => `${v.age_days}d` },
    { key: 'ale', header: 'Annual loss', align: 'right', sortValue: v => v.ale_inr, render: v => <Money v={v.ale_inr} className="font-semibold text-risk-high" /> },
  ]

  return (
    <div className="space-y-6">
      <SectionTitle title="Vulnerabilities" subtitle="Correlated from security telemetry, priced by business impact" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {SEVS.map(s => (
          <button key={s} onClick={() => setSev(sev === s ? null : s)} className={`card card-pad text-left transition ${sev === s ? 'ring-2 ring-brand-500/50' : 'hover:bg-hover/[0.03]'}`}>
            <div className="stat-label">{s}</div>
            <div className="mt-1 text-2xl font-bold text-fg">{num(data.by_severity?.[s] ?? 0)}</div>
          </button>
        ))}
      </div>

      <CardPad>
        <SectionTitle title={`${rows.length} of ${data.count} vulnerabilities`} subtitle="Click severity cards to filter"
          right={
            <div className="flex gap-1.5">
              {Object.keys(data.by_status ?? {}).map(st => (
                <button key={st} onClick={() => setStatus(status === st ? null : st)}
                  className={`chip capitalize ${status === st ? 'bg-brand-600/30 text-brand-100 ring-1 ring-brand-500/40' : 'bg-hover/10 text-body'}`}>
                  {st} · {num(data.by_status[st])}
                </button>
              ))}
            </div>
          } />
        <DataTable columns={cols} rows={rows} initialSort={{ key: 'ale', dir: 'desc' }} />
      </CardPad>

      <Disclaimer />
    </div>
  )
}
