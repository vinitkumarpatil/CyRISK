// Small data-fetching hook: loads a GET endpoint on mount, exposes reload, and
// auto-refreshes when telemetry is simulated (the 'risk-refresh' window event).

import { useCallback, useEffect, useRef, useState } from 'react'
import { get, ApiError } from '../api/client'

export function useApi<T = any>(path: string | null, opts?: { refreshOnTelemetry?: boolean }) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pathRef = useRef(path)
  pathRef.current = path

  const load = useCallback(async () => {
    if (pathRef.current == null) { setLoading(false); return }
    setLoading(true); setError(null)
    try {
      const d = await get<T>(pathRef.current)
      setData(d)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load, path])

  useEffect(() => {
    if (!opts?.refreshOnTelemetry) return
    const h = () => load()
    window.addEventListener('risk-refresh', h)
    return () => window.removeEventListener('risk-refresh', h)
  }, [load, opts?.refreshOnTelemetry])

  return { data, loading, error, reload: load }
}
