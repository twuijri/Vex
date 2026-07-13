import { useCallback, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { AppShell } from '@/components/app-shell'
import { LoginPage } from '@/pages/login'
import { OverviewPage } from '@/pages/overview'
import { GroupsPage } from '@/pages/groups'
import { UsersPage } from '@/pages/users'
import { ProvidersPage } from '@/pages/providers'
import { StatsPage } from '@/pages/stats'
import { PromptPage } from '@/pages/prompt'
import { LogsPage } from '@/pages/logs'
import { useRoute } from '@/lib/router'
import { api, UnauthorizedError, type Me } from '@/lib/api'
import { PageSpinner } from '@/pages/groups'

type AuthState = 'checking' | 'anon' | 'authed'

export default function App() {
  const [auth, setAuth] = useState<AuthState>('checking')
  const [me, setMe] = useState<Me | null>(null)
  const path = useRoute()

  const check = useCallback(async () => {
    try {
      const m = await api.me()
      setMe(m)
      setAuth('authed')
    } catch (e) {
      setAuth(e instanceof UnauthorizedError ? 'anon' : 'anon')
    }
  }, [])

  useEffect(() => {
    check()
  }, [check])

  // Any API call that hits 401 flips us back to the login screen
  useEffect(() => {
    const onUnauthorized = () => setAuth('anon')
    window.addEventListener('vex:unauthorized', onUnauthorized)
    return () => window.removeEventListener('vex:unauthorized', onUnauthorized)
  }, [])

  if (auth === 'checking') {
    return (
      <div className="grid min-h-dvh place-items-center bg-bg spotlight-bg">
        <PageSpinner />
      </div>
    )
  }

  if (auth === 'anon') {
    return <LoginPage onLogin={check} />
  }

  return (
    <AppShell botUsername={me?.bot_username ?? null} onLogout={() => setAuth('anon')}>
      <AnimatePresence mode="wait">
        <motion.div
          key={pageKey(path)}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
        >
          {renderPage(path)}
        </motion.div>
      </AnimatePresence>
    </AppShell>
  )
}

function pageKey(path: string): string {
  if (path.startsWith('/groups')) return '/groups'
  return path
}

function renderPage(path: string) {
  if (path === '/' || path === '') return <OverviewPage />
  if (path.startsWith('/groups')) return <GroupsPage />
  if (path.startsWith('/users')) return <UsersPage />
  if (path.startsWith('/providers')) return <ProvidersPage />
  if (path.startsWith('/stats')) return <StatsPage />
  if (path.startsWith('/prompt')) return <PromptPage />
  if (path.startsWith('/logs')) return <LogsPage />
  return <OverviewPage />
}
