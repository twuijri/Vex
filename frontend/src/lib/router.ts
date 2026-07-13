import { useEffect, useState } from 'react'

// Minimal pathname router. FastAPI serves index.html for any /dashboard*
// path, so deep links + refresh work. Paths here are relative to /dashboard.

const BASE = '/dashboard'

function currentPath(): string {
  const p = window.location.pathname
  if (!p.startsWith(BASE)) return '/'
  const rest = p.slice(BASE.length)
  return rest === '' || rest === '/' ? '/' : rest.replace(/\/$/, '')
}

export function useRoute(): string {
  const [path, setPath] = useState(currentPath)
  useEffect(() => {
    const onPop = () => setPath(currentPath())
    window.addEventListener('popstate', onPop)
    window.addEventListener('vex:navigate', onPop)
    return () => {
      window.removeEventListener('popstate', onPop)
      window.removeEventListener('vex:navigate', onPop)
    }
  }, [])
  return path
}

export function navigate(to: string) {
  const full = BASE + (to === '/' ? '' : to)
  if (full === window.location.pathname) return
  window.history.pushState({}, '', full)
  window.dispatchEvent(new Event('vex:navigate'))
}
