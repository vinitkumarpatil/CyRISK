// Risk Assistant — deterministic NL query interface. Every numeric answer is
// sourced from the computed risk model; the assistant never invents figures.

import { FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, Send, User as UserIcon, ArrowRight, Sparkles } from 'lucide-react'
import { get, post } from '../api/client'
import type { AssistantAnswer } from '../api/types'
import { CardPad, SectionTitle, Disclaimer, Loading } from '../components/ui'
import { inr } from '../lib/format'

interface Turn { q: string; a?: AssistantAnswer; error?: string }

export default function Assistant() {
  const [q, setQ] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { get('/api/assistant/suggestions').then(d => setSuggestions(d.suggestions ?? [])).catch(() => {}) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [turns, busy])

  async function ask(question: string) {
    const question_ = question.trim()
    if (!question_ || busy) return
    setQ(''); setBusy(true)
    setTurns(t => [...t, { q: question_ }])
    try {
      const a = await post<AssistantAnswer>('/api/assistant/query', { question: question_ })
      setTurns(t => { const c = [...t]; c[c.length - 1] = { q: question_, a }; return c })
    } catch (e: any) {
      setTurns(t => { const c = [...t]; c[c.length - 1] = { q: question_, error: e?.message ?? 'Query failed' }; return c })
    } finally { setBusy(false) }
  }

  function submit(e: FormEvent) { e.preventDefault(); ask(q) }

  return (
    <div className="space-y-6">
      <SectionTitle title="Risk Assistant" subtitle="Ask about your risk posture in plain language — answers are computed, not generated" />

      <CardPad className="flex h-[62vh] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {turns.length === 0 && (
            <div className="grid h-full place-items-center text-center text-subtle">
              <div>
                <Bot className="mx-auto mb-3 h-10 w-10 text-subtle" />
                <p>Try a question below, or ask your own.</p>
              </div>
            </div>
          )}
          {turns.map((t, i) => (
            <div key={i} className="space-y-3">
              <div className="flex justify-end">
                <div className="flex max-w-[80%] items-start gap-2 rounded-2xl rounded-tr-sm bg-brand-600/25 px-3.5 py-2.5">
                  <span className="text-sm text-fg">{t.q}</span>
                  <UserIcon className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />
                </div>
              </div>
              {(t.a || t.error) && (
                <div className="flex justify-start">
                  <div className="flex max-w-[85%] items-start gap-2 rounded-2xl rounded-tl-sm border border-hairline-strong bg-elevated/60 px-3.5 py-2.5">
                    <Bot className="mt-0.5 h-4 w-4 shrink-0 text-muted" />
                    <div className="min-w-0 text-sm text-body">
                      {t.error ? <span className="text-risk-high">{t.error}</span> : <AnswerView a={t.a!} />}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          {busy && <div className="flex items-center gap-2 text-sm text-subtle"><Bot className="h-4 w-4" /> Computing…</div>}
          <div ref={endRef} />
        </div>

        {suggestions.length > 0 && turns.length === 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => ask(s)} className="chip inline-flex items-center gap-1 bg-hover/10 text-body hover:bg-hover/15">
                <Sparkles className="h-3 w-3 text-brand-300" /> {s}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={submit} className="mt-3 flex gap-2">
          <input className="input" value={q} onChange={e => setQ(e.target.value)} placeholder="e.g. What is our biggest financial risk?" />
          <button className="btn-primary shrink-0" disabled={busy || !q.trim()}><Send className="h-4 w-4" /></button>
        </form>
      </CardPad>

      <Disclaimer text="Answers are produced by a deterministic intent parser over the computed risk model. Any language model is used only for phrasing — never to generate numbers." />
    </div>
  )
}

function AnswerView({ a }: { a: AssistantAnswer }) {
  if (!a) return null
  if (a.action_required === 'run_optimizer') {
    return (
      <div>
        <p>I can optimize a security portfolio for a budget of <b>{inr(a.budget_inr ?? 0)}</b>.</p>
        <Link to="/optimizer" className="mt-2 inline-flex items-center gap-1 text-brand-300 hover:text-brand-200">Open the optimizer <ArrowRight className="h-3.5 w-3.5" /></Link>
      </div>
    )
  }
  return (
    <div>
      <p className="whitespace-pre-wrap leading-relaxed">{a.answer}</p>
      {a.numbers_source && <div className="mt-2 text-[11px] text-subtle">Source: {a.numbers_source}</div>}
    </div>
  )
}
