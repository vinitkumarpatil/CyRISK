// Fetch-based API client. Reads the bearer token from localStorage and talks to
// the backend via VITE_API_BASE (blank in dev → Vite proxies /api to :8000).

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')
const TOKEN_KEY = 'sih_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  detail: any
  constructor(status: number, detail: any) {
    super(typeof detail === 'string' ? detail : (detail?.detail ?? `Request failed (${status})`))
    this.status = status
    this.detail = detail
  }
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...(extra ?? {}) }
  const t = getToken()
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

async function parse(res: Response): Promise<any> {
  const ct = res.headers.get('content-type') ?? ''
  const body = ct.includes('application/json') ? await res.json().catch(() => null) : await res.text()
  if (!res.ok) {
    // A 401 means the token is missing/expired — clear it so the app returns to login.
    if (res.status === 401) setToken(null)
    throw new ApiError(res.status, body)
  }
  return body
}

export async function get<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders() })
  return parse(res)
}

export async function post<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return parse(res)
}

export async function put<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return parse(res)
}

export async function del<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE', headers: authHeaders() })
  return parse(res)
}

/** Multipart upload for CSV/JSON importers. */
export async function upload<T = any>(path: string, file: File): Promise<T> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: authHeaders(), body: fd })
  return parse(res)
}

/** Trigger a browser download for report files (PDF/JSON), preserving auth. */
export async function download(path: string, fallbackName = 'download'): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders() })
  if (!res.ok) { await parse(res); return }
  const blob = await res.blob()
  const cd = res.headers.get('content-disposition') ?? ''
  const m = cd.match(/filename="?([^"]+)"?/)
  const name = m ? m[1] : fallbackName
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = name
  document.body.appendChild(a); a.click()
  a.remove(); URL.revokeObjectURL(url)
}

export const api = { get, post, put, del, upload, download, getToken, setToken }
