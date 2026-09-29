// Login screen. Pulls demo credentials from the backend so graders can sign in
// with one click; no credentials are hard-coded in the frontend. Split premium
// layout: left = product branding, right = sign-in card + the three demo roles.

import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, Loader2, Sun, Moon, TrendingDown, IndianRupee, Activity } from 'lucide-react'
import { useAuth, fetchDemoUsers } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'
import type { DemoUser } from '../api/types'

export default function Login() {
  const { login, user } = useAuth()
  const { theme, toggle } = useTheme()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [demo, setDemo] = useState<DemoUser[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => { if (user) nav('/') }, [user, nav])
  useEffect(() => { fetchDemoUsers().then(setDemo).catch(() => {}) }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(null); setBusy(true)
    try {
      await login(username, password)
      nav('/')
    } catch (e: any) {
      setErr(e?.message ?? 'Login failed')
    } finally { setBusy(false) }
  }

  function pick(u: DemoUser) { setUsername(u.username); setPassword(u.password); setErr(null) }

  return (
    <div className="relative grid min-h-full lg:grid-cols-2">
      {/* Theme toggle — lets graders preview Day/Night before signing in. */}
      <button
        onClick={toggle}
        title={theme === 'day' ? 'Switch to Night' : 'Switch to Day'}
        aria-label="Toggle theme"
        className="absolute right-4 top-4 z-10 inline-flex items-center gap-1.5 rounded-lg border border-hairline-strong bg-hover/[0.06] px-2.5 py-1.5 text-xs font-medium text-body transition hover:bg-hover/10"
      >
        {theme === 'day' ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
        {theme === 'day' ? 'Night' : 'Day'}
      </button>

      {/* LEFT — branding & value proposition */}
      <div className="relative hidden flex-col justify-between overflow-hidden border-r border-hairline bg-panel/40 p-10 lg:flex">
        <div className="pointer-events-none absolute inset-0 opacity-70"
          style={{ backgroundImage: 'radial-gradient(40rem 40rem at 20% 0%, rgba(79,70,229,0.18), transparent 60%), radial-gradient(36rem 36rem at 90% 100%, rgba(34,211,238,0.14), transparent 55%)' }} />
        <div className="relative">
          <img
            src="/riskquant-logo.webp"
            alt="RiskQuant"
            className="block h-auto w-64 rounded-xl ring-1 ring-hairline"
          />
        </div>

        <div className="relative max-w-md">
          <h1 className="text-3xl font-bold leading-tight tracking-tight text-fg">
            AI-powered continuous cyber risk quantification
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Turn security posture into board-ready numbers — exposure, expected annual loss and
            value-at-risk in ₹ — then optimize where every rupee of security budget goes.
          </p>
          <div className="mt-6 space-y-3">
            <Impact icon={<IndianRupee className="h-4 w-4" />} text="Quantify enterprise risk as expected annual loss in ₹" />
            <Impact icon={<TrendingDown className="h-4 w-4" />} text="Optimize investment by return on security spend (ROSI)" />
            <Impact icon={<Activity className="h-4 w-4" />} text="Continuously re-score as new telemetry arrives" />
          </div>
        </div>

        <div className="relative text-[11px] text-subtle">
          Synthetic demo data · modelled estimates in INR · not a compliance certification.
        </div>
      </div>

      {/* RIGHT — sign-in */}
      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">
          {/* Compact brand for small screens where the left panel is hidden. */}
          <div className="mb-6 lg:hidden">
            <img
              src="/riskquant-logo.webp"
              alt="RiskQuant"
              className="block h-auto w-48 rounded-lg ring-1 ring-hairline"
            />
          </div>

          <h2 className="text-xl font-semibold text-fg">Sign in</h2>
          <p className="mt-1 text-sm text-muted">Use a demo role below, or enter your credentials.</p>

          <form onSubmit={submit} className="mt-6 space-y-4" autoComplete="off">
            <div>
              <label className="stat-label">Username</label>
              <input
                className="input mt-1"
                name="rq_username"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                data-lpignore="true"
                data-1p-ignore="true"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoFocus
                placeholder="ciso"
              />
            </div>
            <div>
              <label className="stat-label">Password</label>
              <input
                className="input mt-1"
                type="password"
                name="rq_password"
                autoComplete="new-password"
                data-lpignore="true"
                data-1p-ignore="true"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••"
              />
            </div>
            {err && <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{err}</div>}
            <button className="btn-primary w-full" disabled={busy || !username || !password}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
              Sign in
            </button>
          </form>

          {demo.length > 0 && (
            <div className="mt-6">
              <div className="mb-2 text-xs uppercase tracking-wider text-subtle">Demo accounts — click to fill</div>
              <div className="space-y-2">
                {demo.map(u => (
                  <button key={u.username} onClick={() => pick(u)} type="button"
                    className="flex w-full items-center justify-between rounded-xl border border-hairline-strong bg-hover/[0.04] px-3 py-2.5 text-left transition hover:border-brand-500/40 hover:bg-hover/[0.08]">
                    <div>
                      <div className="text-sm font-semibold text-fg">{u.name}</div>
                      <div className="mt-0.5 font-mono text-[11px] text-muted">{u.username} / {u.password}</div>
                    </div>
                    <span className="shrink-0 rounded-md bg-brand-600/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-300 ring-1 ring-brand-500/20">{u.role}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Impact({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-body">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-hairline-strong bg-hover/[0.06] text-brand-300">{icon}</span>
      {text}
    </div>
  )
}
