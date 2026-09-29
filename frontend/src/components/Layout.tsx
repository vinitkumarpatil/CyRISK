// App shell: role-aware sidebar navigation + topbar with global demo controls
// (Simulate telemetry → continuous risk re-scoring) and the Day/Night switch.

import { ReactNode, useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Activity, Server, ShieldAlert, ShieldCheck, Lightbulb,
  GitBranch, SlidersHorizontal, BookMarked, Bot, FileText, Radio, BrainCircuit,
  Settings2, LogOut, Zap, Menu, X, Sun, Moon,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { api } from '../api/client'
import { inr } from '../lib/format'
import { useTheme } from '../theme/ThemeContext'

export interface NavItem { to: string; label: string; icon: ReactNode; group: string }

const I = 'h-4 w-4'
export const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard className={I} />, group: 'Overview' },
  { to: '/risk', label: 'Risk Analysis', icon: <Activity className={I} />, group: 'Overview' },
  { to: '/assets', label: 'Assets', icon: <Server className={I} />, group: 'Inventory' },
  { to: '/vulnerabilities', label: 'Vulnerabilities', icon: <ShieldAlert className={I} />, group: 'Inventory' },
  { to: '/controls', label: 'Controls', icon: <ShieldCheck className={I} />, group: 'Inventory' },
  { to: '/recommendations', label: 'Recommendations', icon: <Lightbulb className={I} />, group: 'Decisions' },
  { to: '/scenarios', label: 'What-if Scenarios', icon: <GitBranch className={I} />, group: 'Decisions' },
  { to: '/optimizer', label: 'Investment Optimizer', icon: <SlidersHorizontal className={I} />, group: 'Decisions' },
  { to: '/frameworks', label: 'Frameworks', icon: <BookMarked className={I} />, group: 'Governance' },
  { to: '/assumptions', label: 'Assumptions', icon: <Settings2 className={I} />, group: 'Governance' },
  { to: '/assistant', label: 'Risk Assistant', icon: <Bot className={I} />, group: 'Intelligence' },
  { to: '/model', label: 'ML Model', icon: <BrainCircuit className={I} />, group: 'Intelligence' },
  { to: '/telemetry', label: 'Data Sources', icon: <Radio className={I} />, group: 'Operations' },
  { to: '/reports', label: 'Reports', icon: <FileText className={I} />, group: 'Operations' },
]

const GROUPS = ['Overview', 'Inventory', 'Decisions', 'Governance', 'Intelligence', 'Operations']

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const day = theme === 'day'
  return (
    <button
      onClick={toggle}
      title={day ? 'Switch to Night' : 'Switch to Day'}
      aria-label="Toggle theme"
      className="inline-flex items-center gap-1.5 rounded-lg border border-hairline-strong bg-hover/[0.06] px-2.5 py-1.5 text-xs font-medium text-body transition hover:bg-hover/10"
    >
      {day ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
      <span className="hidden sm:inline">{day ? 'Night' : 'Day'}</span>
    </button>
  )
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex h-full flex-col gap-5 overflow-y-auto p-4">
      {GROUPS.map(g => (
        <div key={g}>
          <div className="px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-subtle">{g}</div>
          <div className="space-y-0.5">
            {NAV.filter(n => n.group === g).map(n => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === '/'}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition ${
                    isActive ? 'bg-brand-600/20 text-brand-200 ring-1 ring-brand-500/30' : 'text-muted hover:bg-hover/[0.06] hover:text-fg'
                  }`
                }
              >
                {n.icon} {n.label}
              </NavLink>
            ))}
          </div>
        </div>
      ))}
    </nav>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [org, setOrg] = useState<string>('')
  const [flash, setFlash] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    // Prefer the org from the authenticated identity; fall back to demo status.
    if (user?.organization) { setOrg(user.organization); return }
    api.get('/api/demo/status').then(s => setOrg(s?.organization ?? '')).catch(() => {})
  }, [user])

  function toast(msg: string) {
    setFlash(msg)
    window.setTimeout(() => setFlash(null), 6000)
  }

  async function simulate() {
    setBusy(true)
    try {
      const r = await api.post('/api/demo/simulate-telemetry')
      toast(`Telemetry ingested — risk ${r.risk_score} (${r.risk_band}), ALE ${inr(r.total_ale_inr)}. Snapshot #${r.snapshot_id}.`)
      window.dispatchEvent(new CustomEvent('risk-refresh'))
    } catch (e: any) {
      toast(e?.message ?? 'Simulation failed')
    } finally { setBusy(false) }
  }

  function doLogout() { logout(); nav('/login') }

  return (
    <div className="flex h-full">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-hairline bg-panel/60 backdrop-blur lg:block">
        <Brand />
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 border-r border-hairline bg-panel">
            <div className="flex items-center justify-between pr-2"><Brand /><button onClick={() => setMobileOpen(false)}><X className="h-5 w-5 text-muted" /></button></div>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-hairline bg-panel/70 px-4 py-3 backdrop-blur">
          <button className="lg:hidden" onClick={() => setMobileOpen(true)}><Menu className="h-5 w-5 text-body" /></button>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <div className="truncate text-sm font-semibold text-fg">{org || 'Cyber Risk Console'}</div>
              {user?.is_demo && (
                <span className="rounded-md border border-amber-400/30 bg-amber-400/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-500">Demo</span>
              )}
            </div>
            <div className="text-[11px] text-subtle">Continuous Cyber Risk Quantification</div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            {(user?.role === 'ciso' || user?.role === 'analyst') && (
              <button className="btn-primary !py-1.5 !px-3 text-xs" onClick={simulate} disabled={busy}>
                <Zap className="h-3.5 w-3.5" /> {busy ? 'Ingesting…' : 'Simulate Telemetry'}
              </button>
            )}
            <ThemeToggle />
            <div className="hidden items-center gap-2 rounded-lg border border-hairline-strong bg-hover/[0.06] px-2.5 py-1.5 sm:flex">
              <div className="text-right">
                <div className="text-xs font-medium text-body">{user?.name}</div>
                <div className="text-[10px] uppercase tracking-wide text-subtle">{user?.role}</div>
              </div>
            </div>
            <button className="btn-ghost !py-1.5 !px-3 text-xs" onClick={doLogout}><LogOut className="h-3.5 w-3.5" /> Logout</button>
          </div>
        </header>

        {flash && (
          <div className="border-b border-brand-500/20 bg-brand-600/10 px-4 py-2 text-sm text-brand-200">{flash}</div>
        )}

        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

function Brand() {
  return (
    <div className="px-4 py-4">
      <img
        src="/riskquant-logo.webp"
        alt="RiskQuant"
        className="block h-auto w-full rounded-xl ring-1 ring-hairline"
      />
    </div>
  )
}
