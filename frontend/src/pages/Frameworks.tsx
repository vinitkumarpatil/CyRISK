// Frameworks — maps internal controls to ISO 27001 / NIST CSF / CIS / RBI / SEBI.
// This is an assessment aid only; it never asserts certification or compliance.

import { useState } from 'react'
import { BookMarked } from 'lucide-react'
import { useApi } from '../lib/useApi'
import type { Framework } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Chip, Disclaimer, StatCard, ProgressBar,
} from '../components/ui'
import { DataTable, Column } from '../components/DataTable'
import { pctRaw, pct, statusChip } from '../lib/format'

interface FwResp {
  count: number
  rollup: { assessment_index: number; frameworks: number; weakest?: string }
  frameworks: Framework[]
  disclaimer: string
}

export default function Frameworks() {
  const { data, loading, error, reload } = useApi<FwResp>('/api/frameworks', { refreshOnTelemetry: true })
  const [active, setActive] = useState(0)
  if (loading) return <Loading label="Assessing frameworks…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const fw = data.frameworks[active]
  const cols: Column<Framework['controls'][number]>[] = [
    { key: 'ref', header: 'Control', render: c => (
      <div><div className="font-mono text-xs text-brand-300">{c.control_ref}</div>
        <div className="text-body">{c.title}</div></div>
    ) },
    { key: 'cat', header: 'Category', render: c => <span className="text-muted">{c.category}</span> },
    { key: 'map', header: 'Mapped to', render: c => c.internal_control_key ? <Chip className="bg-hover/10 text-body">{c.internal_control_key}</Chip> : <span className="text-subtle">—</span> },
    { key: 'eff', header: 'Effectiveness', align: 'right', sortValue: c => c.effectiveness ?? -1, render: c => c.effectiveness == null ? <span className="text-subtle">n/a</span> : (
      <div className="ml-auto w-24"><ProgressBar value={c.effectiveness} /><div className="mt-0.5 text-right text-[11px] text-subtle">{pct(c.effectiveness)}</div></div>
    ) },
    { key: 'st', header: 'Status', render: c => <Chip className={statusChip(c.status)}>{c.status}</Chip> },
  ]

  return (
    <div className="space-y-6">
      <SectionTitle title="Framework Mapping & Assessment" subtitle="Internal control posture expressed against common frameworks" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Assessment index" value={pctRaw(data.rollup.assessment_index)} icon={<BookMarked className="h-4 w-4" />} accent="text-brand-300" />
        <StatCard label="Frameworks assessed" value={data.rollup.frameworks} />
        <StatCard label="Weakest area" value={<span className="text-base">{data.rollup.weakest ?? '—'}</span>} accent="text-risk-high" />
        <StatCard label="Total controls mapped" value={data.frameworks.reduce((s, f) => s + f.control_count, 0)} />
      </div>

      <div className="flex flex-wrap gap-2">
        {data.frameworks.map((f, i) => (
          <button key={f.key} onClick={() => setActive(i)}
            className={`rounded-xl border px-3 py-2 text-left text-sm transition ${i === active ? 'border-brand-500/50 bg-brand-600/15 text-brand-100' : 'border-hairline-strong bg-hover/[0.02] text-body hover:bg-hover/5'}`}>
            <div className="font-semibold">{f.name}</div>
            <div className="text-[11px] text-subtle">{pctRaw(f.assessment_index)} · {f.control_count} controls</div>
          </button>
        ))}
      </div>

      {fw && (
        <CardPad>
          <SectionTitle title={fw.full_name || fw.name} subtitle={`Version ${fw.version} · assessment index ${pctRaw(fw.assessment_index)}`} />
          <div className="mb-4 flex flex-wrap gap-2">
            {Object.entries(fw.counts).map(([k, v]) => (
              <Chip key={k} className={statusChip(k)}>{k}: {v}</Chip>
            ))}
          </div>
          <DataTable columns={cols} rows={fw.controls} initialSort={{ key: 'eff', dir: 'asc' }} />
          <p className="mt-3 text-[11px] text-amber-200/70">{fw.disclaimer}</p>
        </CardPad>
      )}

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
