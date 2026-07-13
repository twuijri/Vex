import { useState } from 'react'
import { motion } from 'framer-motion'
import { KeyRound, Loader2 } from 'lucide-react'
import { BrandMark } from '@/components/brand-mark'
import { Button } from '@/components/ui/button'
import { SecretField } from '@/components/ui/field'
import { api } from '@/lib/api'

export function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password || busy) return
    setBusy(true)
    setError('')
    try {
      await api.login(password)
      onLogin()
    } catch (err) {
      setError(err instanceof Error && err.message !== 'unauthorized' ? err.message : 'كلمة المرور غير صحيحة')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-dvh place-items-center bg-bg p-4 spotlight-bg">
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', bounce: 0.22, duration: 0.6 }}
        className="w-full max-w-sm rounded-3xl gradient-border glass-card p-8 shadow-card"
      >
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <BrandMark size={52} />
          <div>
            <h1 className="text-2xl font-bold tracking-tight wordmark">Vex</h1>
            <p className="mt-1 text-sm text-muted">لوحة تحكم بوت الحماية</p>
          </div>
        </div>

        <form onSubmit={submit}>
          <SecretField
            label="كلمة المرور"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 rounded-xl border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-danger"
            >
              {error}
            </motion.p>
          )}
          <Button type="submit" className="w-full" disabled={busy || !password}>
            {busy ? <Loader2 className="animate-spin" /> : <KeyRound />}
            دخول
          </Button>
        </form>
      </motion.div>
    </div>
  )
}
