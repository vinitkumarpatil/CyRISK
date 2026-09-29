// Assets — inventory with transparent business criticality and the annual loss
// each asset carries. Row click loads the per-asset breakdown + findings.

import { useEffect, useState } from 'react'
import { Server, Globe, Lock, Plus, Pencil, Trash2, Loader2 } from 'lucide-react'
import { useApi } from '../lib/useApi'
import { get, post, put, del } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, ProgressBar, Explain, Disclaimer, StatCard,
} from '../components/ui'
import { DataTable, Column } from '../components/DataTable'
import { Modal } from '../components/Modal'
import { pct, num } from '../lib/format'

interface AssetRow {
  id: number; name: string; asset_type: string; environment: string; bu_name: string
  internet_facing: boolean; owner: string; records_count: number
  business_value_inr: number; criticality: number; tier: string; ale_inr: number; exposure_inr: number; vuln_count: number
}

function tierColor(tier: string) {
  const t = tier.toLowerCase()
  if (t.includes('crown') || t.includes('critical')) return 'bg-risk-critical/15 text-risk-critical ring-1 ring-risk-critical/30'
  if (t.includes('high')) return 'bg-risk-high/15 text-risk-high ring-1 ring-risk-high/30'
  if (t.includes('med')) return 'bg-risk-medium/15 text-risk-medium ring-1 ring-risk-medium/30'
  return 'bg-hover/10 text-body ring-1 ring-white/10'
}

const ASSET_TYPES = ['server', 'database', 'endpoint', 'network', 'saas', 'app']
const ENVIRONMENTS = ['production', 'staging', 'development', 'dr']
const FACTORS = [
  { key: 'data_sensitivity', label: 'Data sensitivity', hint: 'How sensitive is the data it holds?' },
  { key: 'operational_criticality', label: 'Operational criticality', hint: 'How badly does downtime hurt operations?' },
  { key: 'regulatory_importance', label: 'Regulatory importance', hint: 'RBI/SEBI/ISO exposure if compromised?' },
] as const

interface FormState {
  name: string; asset_type: string; environment: string; owner: string; ip_or_host: string
  internet_facing: boolean; business_value_inr: string; revenue_impact_per_day_inr: string
  data_sensitivity: number; operational_criticality: number; regulatory_importance: number; records_count: string
}

const BLANK: FormState = {
  name: '', asset_type: 'server', environment: 'production', owner: '', ip_or_host: '',
  internet_facing: false, business_value_inr: '', revenue_impact_per_day_inr: '',
  data_sensitivity: 2, operational_criticality: 2, regulatory_importance: 2, records_count: '',
}

function AssetForm({ initial, assetId, onDone, onCancel }: {
  initial: FormState; assetId?: number; onDone: () => void; onCancel: () => void
}) {
  const [f, setF] = useState<FormState>(initial)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const set = (patch: Partial<FormState>) => setF(s => ({ ...s, ...patch }))
  const editing = assetId != null

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!f.name.trim()) { setErr('Asset name is required.'); return }
    setErr(null); setBusy(true)
    try {
      // org_id is intentionally NOT sent — the backend derives it from the token.
      const payload = {
        name: f.name.trim(), asset_type: f.asset_type, environment: f.environment,
        owner: f.owner.trim(), ip_or_host: f.ip_or_host.trim(), internet_facing: f.internet_facing,
        business_value_inr: Number(f.business_value_inr) || 0,
        revenue_impact_per_day_inr: Number(f.revenue_impact_per_day_inr) || 0,
        data_sensitivity: f.data_sensitivity, operational_criticality: f.operational_criticality,
        regulatory_importance: f.regulatory_importance, records_count: Number(f.records_count) || 0,
      }
      if (editing) await put(`/api/assets/${assetId}`, payload) // update in place, no duplicate
      else await post('/api/assets', payload)
      onDone()
    } catch (e: any) {
      setErr(e?.message ?? 'Could not save asset.')
    } finally { setBusy(false) }
  }

  const L = 'stat-label'
  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className={L}>Asset name *</label>
        <input className="input mt-1" value={f.name} autoFocus placeholder="e.g. Core Banking DB"
          onChange={e => set({ name: e.target.value })} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={L}>Type</label>
          <select className="input mt-1" value={f.asset_type} onChange={e => set({ asset_type: e.target.value })}>
            {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className={L}>Environment</label>
          <select className="input mt-1" value={f.environment} onChange={e => set({ environment: e.target.value })}>
            {ENVIRONMENTS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={L}>Owner / team</label>
          <input className="input mt-1" value={f.owner} placeholder="e.g. Payments"
            onChange={e => set({ owner: e.target.value })} />
        </div>
        <div>
          <label className={L}>Hostname / IP</label>
          <input className="input mt-1" value={f.ip_or_host} placeholder="optional"
            onChange={e => set({ ip_or_host: e.target.value })} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={L}>Business value (₹)</label>
          <input className="input mt-1" type="number" min={0} value={f.business_value_inr} placeholder="0"
            onChange={e => set({ business_value_inr: e.target.value })} />
        </div>
        <div>
          <label className={L}>Revenue impact / day of downtime (₹)</label>
          <input className="input mt-1" type="number" min={0} value={f.revenue_impact_per_day_inr} placeholder="0"
            onChange={e => set({ revenue_impact_per_day_inr: e.target.value })} />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {FACTORS.map(fac => (
          <div key={fac.key} title={fac.hint}>
            <label className={L}>{fac.label}</label>
            <select className="input mt-1" value={f[fac.key]}
              onChange={e => set({ [fac.key]: Number(e.target.value) } as Partial<FormState>)}>
              {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={L}>Records held</label>
          <input className="input mt-1" type="number" min={0} value={f.records_count} placeholder="0"
            onChange={e => set({ records_count: e.target.value })} />
        </div>
        <label className="flex items-end gap-2 pb-2 text-sm text-body">
          <input type="checkbox" className="h-4 w-4 rounded border-hairline-strong bg-hover/5"
            checked={f.internet_facing} onChange={e => set({ internet_facing: e.target.checked })} />
          Internet-facing
        </label>
      </div>
      <p className="text-[11px] text-subtle">
        Criticality (0–100) is derived by the risk engine from these factors — it isn't entered directly.
      </p>
      {err && <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{err}</div>}
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" className="btn-ghost" onClick={onCancel} disabled={busy}>Cancel</button>
        <button className="btn-primary" disabled={busy || !f.name.trim()}>
          {editing ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {busy ? 'Saving…' : editing ? 'Save changes' : 'Create asset'}
        </button>
      </div>
    </form>
  )
}

function assetToForm(a: any): FormState {
  return {
    name: a.name ?? '', asset_type: a.asset_type ?? 'server', environment: a.environment ?? 'production',
    owner: a.owner ?? '', ip_or_host: a.ip_or_host ?? '', internet_facing: !!a.internet_facing,
    business_value_inr: String(a.business_value_inr ?? ''),
    revenue_impact_per_day_inr: String(a.revenue_impact_per_day_inr ?? ''),
    data_sensitivity: a.data_sensitivity ?? 2, operational_criticality: a.operational_criticality ?? 2,
    regulatory_importance: a.regulatory_importance ?? 2, records_count: String(a.records_count ?? ''),
  }
}




export default function Assets() {
  const { user } = useAuth()
  const { data, loading, error, reload } = useApi<{ count: number; assets: AssetRow[] }>('/api/assets', { refreshOnTelemetry: true })
  const [sel, setSel] = useState<AssetRow | null>(null)
  const [detail, setDetail] = useState<any>(null)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<{ id: number; form: FormState } | null>(null)
  const [deleting, setDeleting] = useState<AssetRow | null>(null)
  const [delBusy, setDelBusy] = useState(false)
  const [delErr, setDelErr] = useState<string | null>(null)

  // Real-org rows are all non-demo and editable; the demo tenant's showcase
  // (Meghdoot) stays read-only, matching the backend's 403 on demo assets.
  const canEdit = (user?.role === 'ciso' || user?.role === 'analyst') && !user?.is_demo

  useEffect(() => {
    if (!sel) { setDetail(null); return }
    let alive = true
    get(`/api/assets/${sel.id}`).then(d => { if (alive) setDetail(d) }).catch(() => {})
    return () => { alive = false }
  }, [sel])

  function refreshAll() {
    reload()
    window.dispatchEvent(new CustomEvent('risk-refresh')) // refresh dashboard/risk views
  }

  function onSaved() {
    setAdding(false)
    setEditing(null)
    refreshAll()
  }

  async function openEdit(row: AssetRow) {
    // The list payload lacks the raw criticality factors, so fetch the full
    // asset to pre-fill every field accurately.
    try {
      const d = await get(`/api/assets/${row.id}`)
      setEditing({ id: row.id, form: assetToForm(d.asset) })
    } catch { /* ignore — button just won't open */ }
  }

  async function confirmDelete() {
    if (!deleting) return
    setDelErr(null); setDelBusy(true)
    try {
      await del(`/api/assets/${deleting.id}`)
      setDeleting(null)
      refreshAll()
    } catch (e: any) {
      setDelErr(e?.message ?? 'Could not delete asset.')
    } finally { setDelBusy(false) }
  }

  if (loading) return <Loading label="Loading assets…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const addBtn = canEdit ? (
    <button className="btn-primary !py-1.5 !px-3 text-sm" onClick={() => setAdding(true)}>
      <Plus className="h-4 w-4" /> Add Asset
    </button>
  ) : null

  const modals = (
    <>
      <Modal open={adding} onClose={() => setAdding(false)} title="Add a business asset">
        <AssetForm initial={BLANK} onDone={onSaved} onCancel={() => setAdding(false)} />
      </Modal>
      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit asset">
        {editing && (
          <AssetForm initial={editing.form} assetId={editing.id}
            onDone={onSaved} onCancel={() => setEditing(null)} />
        )}
      </Modal>
      <Modal open={!!deleting} onClose={() => setDeleting(null)} title="Delete asset">
        <div className="space-y-4">
          <p className="text-sm text-body">
            Delete <span className="font-semibold text-fg">{deleting?.name}</span>? This action cannot be undone.
          </p>
          {delErr && <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{delErr}</div>}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setDeleting(null)} disabled={delBusy}>Cancel</button>
            <button className="btn-primary !bg-risk-high/90 hover:!bg-risk-high" onClick={confirmDelete} disabled={delBusy}>
              {delBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />} Delete asset
            </button>
          </div>
        </div>
      </Modal>
    </>
  )

  // Empty workspace (e.g. a freshly registered organization) — guide the user
  // to create their first asset instead of showing zeroed-out stat cards.
  if (data.count === 0) {
    return (
      <div className="space-y-6">
        <SectionTitle title="Assets" subtitle="Business criticality drives loss magnitude" right={addBtn} />
        <CardPad>
          <div className="flex flex-col items-center gap-3 py-12 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-600/15 text-brand-300"><Server className="h-6 w-6" /></div>
            <div className="text-base font-semibold text-fg">No assets yet</div>
            <p className="max-w-sm text-sm text-muted">Add your first business asset to begin risk quantification. Assets you add here belong only to your organization.</p>
            {canEdit
              ? <button className="btn-primary mt-1" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add your first asset</button>
              : <p className="text-xs text-subtle">Ask a CISO or analyst on your team to add assets.</p>}
          </div>
        </CardPad>
        <Disclaimer />
        {modals}
      </div>
    )
  }

  const totalAle = data.assets.reduce((s, a) => s + a.ale_inr, 0)
  const exposed = data.assets.filter(a => a.internet_facing).length
  const cols: Column<AssetRow>[] = [
    { key: 'name', header: 'Asset', render: a => (
      <div><div className="flex items-center gap-1.5 font-medium text-fg">{a.internet_facing ? <Globe className="h-3.5 w-3.5 text-risk-high" /> : <Lock className="h-3.5 w-3.5 text-subtle" />}{a.name}</div>
        <div className="text-xs text-subtle">{a.asset_type} · {a.bu_name}</div></div>
    ) },
    { key: 'tier', header: 'Tier', render: a => <Chip className={tierColor(a.tier)}>{a.tier}</Chip> },
    { key: 'crit', header: 'Criticality', sortValue: a => a.criticality, render: a => (
      <div className="w-28"><ProgressBar value={a.criticality / 100} /><div className="mt-0.5 text-[11px] text-subtle">{a.criticality.toFixed(1)}/100</div></div>
    ) },
    { key: 'vulns', header: 'Vulns', align: 'right', sortValue: a => a.vuln_count, render: a => num(a.vuln_count) },
    { key: 'exp', header: 'Exposure', align: 'right', sortValue: a => a.exposure_inr, render: a => <Money v={a.exposure_inr} /> },
    { key: 'ale', header: 'Annual loss', align: 'right', sortValue: a => a.ale_inr, render: a => <Money v={a.ale_inr} className="font-semibold text-risk-high" /> },
  ]
  if (canEdit) {
    cols.push({
      key: 'actions', header: '', align: 'right', render: a => (
        <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
          <button title="Edit asset" onClick={() => openEdit(a)}
            className="rounded-lg p-1.5 text-muted hover:bg-hover/10 hover:text-brand-300"><Pencil className="h-4 w-4" /></button>
          <button title="Delete asset" onClick={() => setDeleting(a)}
            className="rounded-lg p-1.5 text-muted hover:bg-risk-high/15 hover:text-risk-high"><Trash2 className="h-4 w-4" /></button>
        </div>
      ),
    })
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Assets" subtitle="Business criticality drives loss magnitude — click an asset for its derivation" right={addBtn} />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Assets" value={num(data.count)} icon={<Server className="h-4 w-4" />} />
        <StatCard label="Internet-facing" value={num(exposed)} accent="text-risk-high" />
        <StatCard label="Aggregate annual loss" value={<Money v={totalAle} />} accent="text-risk-high" />
        <StatCard label="Avg criticality" value={`${(data.assets.reduce((s, a) => s + a.criticality, 0) / (data.assets.length || 1)).toFixed(0)}/100`} />
      </div>
      <CardPad>
        <DataTable columns={cols} rows={data.assets} initialSort={{ key: 'ale', dir: 'desc' }} onRowClick={setSel} />
        <Explain title="How criticality is derived">
          Criticality blends business value, revenue-impact per day of downtime, data sensitivity, operational criticality and
          regulatory importance into a 0–1 score. It scales an asset's exposure and the impact components of every finding on it,
          so more business-critical assets carry proportionally larger expected loss.
        </Explain>
      </CardPad>
      <Disclaimer />
      <Modal open={!!sel} onClose={() => setSel(null)} wide title={sel?.name ?? ''}>
        {!detail ? <Loading /> : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Criticality" value={`${(detail.criticality?.score ?? 0).toFixed(1)}/100`} sub={detail.criticality?.tier} />
              <StatCard label="Annual loss" value={<Money v={detail.ale_inr} />} accent="text-risk-high" />
              <StatCard label="Exposure" value={<Money v={detail.exposure_inr} />} />
              <StatCard label="Findings" value={num(detail.findings?.length ?? 0)} />
            </div>
            {detail.criticality?.factors?.length > 0 && (
              <div className="rounded-xl border border-hairline bg-elevated/40 p-3">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Criticality factors</div>
                {detail.criticality.factors.map((f: any) => (
                  <div key={f.name} className="flex items-center justify-between border-b border-hairline py-1 text-sm last:border-0">
                    <span className="text-muted">{f.name.replace(/_/g, ' ')} <span className="text-subtle">· weight {pct(f.weight, 0)}</span></span>
                    <span className="font-medium text-fg">+{(f.contribution ?? 0).toFixed(1)}</span>
                  </div>
                ))}
                {detail.criticality.formula && <div className="mt-2 font-mono text-[11px] text-subtle">{detail.criticality.formula}</div>}
              </div>
            )}
            {detail.findings?.length > 0 && (
              <div>
                <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Findings on this asset</div>
                <DataTable
                  dense
                  columns={[
                    { key: 't', header: 'Finding', render: (f: any) => <span className="text-body">{f.title}</span> },
                    { key: 's', header: 'Severity', render: (f: any) => <Chip className={tierColor(f.severity)}>{f.severity}</Chip> },
                    { key: 'a', header: 'ALE', align: 'right', sortValue: (f: any) => f.ale_inr, render: (f: any) => <Money v={f.ale_inr} /> },
                  ]}
                  rows={detail.findings}
                  initialSort={{ key: 'a', dir: 'desc' }}
                />
              </div>
            )}
            {detail.ml_features && (
              <Explain title="ML feature vector for this asset">
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 font-mono text-[11px]">
                  {Object.entries(detail.ml_features).map(([k, v]) => (
                    <div key={k} className="flex justify-between"><span className="text-subtle">{k}</span><span className="text-body">{typeof v === 'number' ? (v as number).toFixed(3) : String(v)}</span></div>
                  ))}
                </div>
              </Explain>
            )}
          </div>
        )}
      </Modal>
      {modals}
    </div>
  )
}
