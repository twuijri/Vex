import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, XCircle } from 'lucide-react'

type Toast = { id: number; kind: 'success' | 'error'; text: string }

const ToastCtx = createContext<(kind: Toast['kind'], text: string) => void>(() => {})

export function useToast() {
  return useContext(ToastCtx)
}

let nextId = 1

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((kind: Toast['kind'], text: string) => {
    const id = nextId++
    setToasts((t) => [...t, { id, kind, text }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200)
  }, [])

  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed bottom-5 start-1/2 z-[100] flex w-[min(92vw,26rem)] -translate-x-1/2 rtl:translate-x-1/2 flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 16, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.97 }}
              transition={{ type: 'spring', bounce: 0.25, duration: 0.45 }}
              className="pointer-events-auto flex items-center gap-2.5 rounded-2xl border border-border glass-card px-4 py-3 text-sm shadow-card"
            >
              {t.kind === 'success'
                ? <CheckCircle2 className="size-4.5 shrink-0 text-success" />
                : <XCircle className="size-4.5 shrink-0 text-danger" />}
              <span className="min-w-0 flex-1">{t.text}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}
