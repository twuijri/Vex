import { useCallback, useEffect, useRef, useState } from 'react'
import { UnauthorizedError } from '@/lib/api'

/**
 * Small data hook: fetch on mount, expose refresh(), optional polling.
 * On 401 it fires the global logout event so the app shows the login screen.
 */
export function useData<T>(fetcher: () => Promise<T>, pollMs?: number) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const refresh = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      setData(await fetcherRef.current())
      setError(null)
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        window.dispatchEvent(new Event('vex:unauthorized'))
        return
      }
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!pollMs) return
    const t = setInterval(() => refresh(true), pollMs)
    return () => clearInterval(t)
  }, [pollMs, refresh])

  return { data, loading, error, refresh }
}
