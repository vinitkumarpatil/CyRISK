// Auth state: logs in via POST /api/auth/login, persists token + user, restores
// the session on reload by validating the stored token against /api/auth/me.

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api, setToken } from '../api/client'
import type { User, LoginResponse, DemoUser } from '../api/types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (body: RegisterBody) => Promise<void>
  logout: () => void
}

export interface RegisterBody {
  company_name: string
  admin_name: string
  username: string
  password: string
  sector?: string
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On mount, if a token is present, confirm it still resolves to a user.
  useEffect(() => {
    let alive = true
    async function restore() {
      if (!api.getToken()) { setLoading(false); return }
      try {
        const me = await api.get<User>('/api/auth/me')
        if (alive) setUser(me)
      } catch {
        setToken(null)
      } finally {
        if (alive) setLoading(false)
      }
    }
    restore()
    return () => { alive = false }
  }, [])

  async function login(username: string, password: string) {
    const res = await api.post<LoginResponse>('/api/auth/login', { username, password })
    setToken(res.token)
    setUser(res.user)
  }

  async function register(body: RegisterBody) {
    const res = await api.post<LoginResponse>('/api/auth/register', body)
    setToken(res.token)
    setUser(res.user)
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

/** Fetch the demo credentials shown on the login screen. */
export async function fetchDemoUsers(): Promise<DemoUser[]> {
  return api.get<DemoUser[]>('/api/auth/demo-users')
}
