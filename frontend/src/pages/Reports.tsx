// Reports — evidence-based executive/technical reports rendered by the backend
// (PDF via reportlab, or JSON). Generated reports are listed and downloadable.

import { useEffect, useState } from 'react'
import { FileText, Download, FileJson, FileType2 } from 'lucide-react'
import { get, post, api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import {
  CardPad, SectionTitle, Disclaimer, Chip, Loading,
} from '../components/ui'
import { shortDate, inr } from '../lib/format'

interface Report { id: number | string; kind: string; fmt: string; title: string; created_at?: string; download_url?: string }

export default function Reports() {
  const { user } = useAuth()
  const canGenerate = user?.role === 'ciso' || user?.role === 'analyst'
  const [kind, setKind] = useState<'executive' | 'technical'>('executive')
  const [fmt, setFmt] = useState<'pdf' | 'json'>('pdf')
  const [budget, setBudget] = useState(20_000_000)
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  async function loadList() {
    try { const d = await get('/api/reports'); setReports(d.reports ?? d ?? []) }
    catch { /* ignore */ } finally { setLoading(false) }
  }
  useEffect(() => { loadList() }, [])

  async function generate() {
    setBusy(true); setMsg(null)
    try {
      const r = await post('/api/reports/generate', { kind, fmt, budget_inr: budget })
      setMsg(`Generated: ${r.title}`)
      await loadList()
      if (r.id != null) await api.download(`/api/reports/${r.id}/download`, `${kind}_report.${fmt}`)
    } catch (e: any) { setMsg(e?.message ?? 'Generation failed') } finally { setBusy(false) }
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Reports" subtitle="Board-ready evidence with the numbers, assumptions and disclaimers baked in" />

      <div className="grid gap-4 lg:grid-cols-2">
        {(['executive', 'technical'] as const).map(k => (
          <button key={k} onClick={() => setKind(k)}
            className={`card card-pad text-left transition ${kind === k ? 'border-brand-500/50 ring-1 ring-brand-500/30' : 'hover:bg-hover/[0.03]'}`}>
            <div className="flex items-center gap-2"><FileText className="h-5 w-5 text-brand-300" /><span className="font-semibold capitalize text-fg">{k} report</span></div>
            <p className="mt-1.5 text-sm text-muted">
              {k === 'executive'
                ? 'Monetary risk headline, top drivers, recommended investments and ROSI — for leadership.'
                : 'Full findings, per-control effectiveness, model metrics and framework assessment — for practitioners.'}
            </p>
          </button>
        ))}
      </div>

      {canGenerate ? (
        <CardPad>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="stat-label">Format</label>
              <div className="mt-1.5 flex gap-1.5">
                <button onClick={() => setFmt('pdf')} className={`chip ${fmt === 'pdf' ? 'bg-brand-600/30 text-brand-100 ring-1 ring-brand-500/40' : 'bg-hover/10 text-body'}`}><FileType2 className="h-3.5 w-3.5" /> PDF</button>
                <button onClick={() => setFmt('json')} className={`chip ${fmt === 'json' ? 'bg-brand-600/30 text-brand-100 ring-1 ring-brand-500/40' : 'bg-hover/10 text-body'}`}><FileJson className="h-3.5 w-3.5" /> JSON</button>
              </div>
            </div>
            <div className="min-w-[200px] flex-1">
              <label className="stat-label">Optimizer budget for report ({inr(budget)})</label>
              <input type="range" min={1_000_000} max={100_000_000} step={1_000_000} value={budget} onChange={e => setBudget(Number(e.target.value))} className="mt-2 w-full accent-brand-500" />
            </div>
            <button className="btn-primary" onClick={generate} disabled={busy}><Download className="h-4 w-4" /> {busy ? 'Generating…' : `Generate ${kind} ${fmt.toUpperCase()}`}</button>
          </div>
          {msg && <div className="mt-3 text-sm text-brand-200">{msg}</div>}
        </CardPad>
      ) : (
        <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200/80">
          Your role (<b>{user?.role}</b>) can view and download existing reports. Generating new reports requires the CISO or analyst role.
        </div>
      )}

      <CardPad>
        <SectionTitle title="Generated reports" />
        {loading ? <Loading /> : reports.length === 0 ? (
          <div className="py-8 text-center text-sm text-subtle">No reports yet.</div>
        ) : (
          <div className="space-y-2">
            {reports.map(r => (
              <div key={String(r.id)} className="flex items-center justify-between rounded-xl border border-hairline bg-elevated/40 px-3.5 py-2.5">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-subtle" />
                  <div>
                    <div className="text-sm font-medium text-fg">{r.title}</div>
                    <div className="text-xs text-subtle"><span className="capitalize">{r.kind}</span> · {r.fmt?.toUpperCase()} {r.created_at && `· ${shortDate(r.created_at)}`}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Chip className="bg-hover/10 text-body uppercase">{r.fmt}</Chip>
                  <button className="btn-ghost !py-1.5 !px-3 text-xs" onClick={() => api.download(`/api/reports/${r.id}/download`, `${r.kind}_report.${r.fmt}`)}>
                    <Download className="h-3.5 w-3.5" /> Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardPad>

      <Disclaimer />
    </div>
  )
}
