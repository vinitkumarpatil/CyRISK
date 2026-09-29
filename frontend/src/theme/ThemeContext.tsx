// Day / Night theme provider. Persists the choice to localStorage and toggles a
// `theme-day` class on <html>; every semantic Tailwind token (surface/panel/
// body/…) resolves through CSS variables, so the whole app adapts instantly.
// Charts read the palette below because Recharts colours are JS props, not CSS.

import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from 'react'

export type Theme = 'day' | 'night'
const STORAGE_KEY = 'sih_theme'

interface ThemeCtx {
  theme: Theme
  toggle: () => void
  setTheme: (t: Theme) => void
  /** Theme-aware colours for Recharts (which can't use CSS classes). */
  chart: {
    axis: string
    grid: string
    tooltipBg: string
    tooltipBorder: string
    tooltipLabel: string
    tooltipItem: string
    legend: string
    cursor: string
  }
}

const NIGHT_CHART: ThemeCtx['chart'] = {
  axis: '#64748b', grid: '#1e293b', tooltipBg: '#0b1220', tooltipBorder: '#1e293b',
  tooltipLabel: '#cbd5e1', tooltipItem: '#e2e8f0', legend: '#94a3b8', cursor: 'rgba(255,255,255,0.04)',
}
const DAY_CHART: ThemeCtx['chart'] = {
  axis: '#64748b', grid: '#e2e8f0', tooltipBg: '#ffffff', tooltipBorder: '#e2e8f0',
  tooltipLabel: '#334155', tooltipItem: '#0f172a', legend: '#475569', cursor: 'rgba(15,23,42,0.05)',
}

const Ctx = createContext<ThemeCtx | null>(null)

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'day' || saved === 'night') return saved
  } catch { /* ignore */ }
  return 'night' // default: preserve the existing dark console look
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(initialTheme)

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('theme-day', theme === 'day')
    try { localStorage.setItem(STORAGE_KEY, theme) } catch { /* ignore */ }
  }, [theme])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggle = useCallback(() => setThemeState(t => (t === 'day' ? 'night' : 'day')), [])

  const value = useMemo<ThemeCtx>(() => ({
    theme, toggle, setTheme, chart: theme === 'day' ? DAY_CHART : NIGHT_CHART,
  }), [theme, toggle, setTheme])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useTheme(): ThemeCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error('useTheme must be used within ThemeProvider')
  return c
}
