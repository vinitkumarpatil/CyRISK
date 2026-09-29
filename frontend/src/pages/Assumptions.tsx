// Assumptions — the tunable levers behind every figure (breach cost per record,
// downtime rates, threat pressure…). Editing one recomputes the whole model.

import { useEffect, useMemo, useState } from 'react'
import { Settings2, Save } from 'lucide-react'
import { get, put } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Assumption } from '../api/types'
import {
  Loading, ErrorState, CardPad, SectionTitle, Disclaimer, Chip,
} from '../components/ui'

export default function Assumptions() {
  const { user } = useAuth()
  const canEdit = user?.role === 'ciso' || user?.role === 'analyst'
  const [items, setItems] = useState<Assumption[]>([])
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [savingKey, setSavingKey] = useState<string | null>(null)
  const [note, setNote] = useState<string>('')

  async function load() {
    setLoading(true)
    try {
      const d = await get('/api/assumptions')
      setItems(d.assumptions ?? [])
      setNote(d.note ?? '')
    } catch (e: any) { setError(e?.message ?? 'Failed to load') } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const groups = useMemo(() => {
    const m: Record<string, Assumption[]> = {}
    for (const a of items) (m[a.category] ??= []).push(a)
    return m
  }, [items])

  async function save(a: Assumption) {
    const raw = draft[a.key]
    if (raw === undefined || raw === '') return
    const value = Number(raw)
    if (Number.isNaN(value) || value < 0) return
    setSavingKey(a.key)
    try {
      await put('/api/assumptions', { key: a.key, value })
      setDraft(d => { const n = { ...d }; delete n[a.key]; return n })
      await load()
      window.dispatchEvent(new CustomEvent('risk-refresh'))
    } catch (e: any) { setError(e?.message ?? 'Update failed') } finally { setSavingKey(null) }
  }

  if (loading) return <Loading label="Loading assumptions…" />
  if (error && !items.length) return <ErrorState message={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <SectionTitle title="Model Assumptions" subtitle="Transparent, editable parameters — changes recompute the entire risk model" />

      {!canEdit && (
        <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200/80">
          Your role (<b>{user?.role}</b>) can view assumptions. Editing requires the CISO or analyst role.
        </div>
      )}
      {error && <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{error}</div>}

      {Object.entries(groups).map(([cat, list]) => (
        <CardPad key={cat}>
          <SectionTitle title={cat} right={<Chip className="bg-hover/10 text-muted"><Settings2 className="h-3 w-3" /> {list.length}</Chip>} />
          <div className="space-y-3">
            {list.map(a => {
              const editing = draft[a.key] !== undefined
              return (
                <div key={a.key} className="flex flex-wrap items-center gap-3 border-b border-hairline py-2.5 last:border-0">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-fg">{a.label}</div>
                    <div className="text-xs text-subtle">{a.description}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {canEdit && a.editable ? (
                      <>
                        <input
                          type="number" min={0} step="any"
                          className="input w-36 !py-1.5 text-right"
                          value={editing ? draft[a.key] : String(a.value)}
                          onChange={e => setDraft(d => ({ ...d, [a.key]: e.target.value }))}
                        />
                        <span className="w-14 text-xs text-subtle">{a.unit}</span>
                        <button className="btn-primary !py-1.5 !px-3 text-xs disabled:opacity-40" disabled={!editing || savingKey === a.key} onClick={() => save(a)}>
                          <Save className="h-3.5 w-3.5" /> {savingKey === a.key ? '…' : 'Save'}
                        </button>
                      </>
                    ) : (
                      <div className="text-right">
                        <div className="font-semibold tabular-nums text-fg">{a.value_display ?? a.value}</div>
                        <div className="text-[11px] text-subtle">{a.unit}</div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardPad>
      ))}

      <Disclaimer text={note || 'Assumptions are documented, editable inputs. All downstream figures are recomputed from them — nothing is hard-coded.'} />
    </div>
  )
}
