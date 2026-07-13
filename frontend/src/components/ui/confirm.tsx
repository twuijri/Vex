import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

type ConfirmOpts = { title: string; body?: string; confirmLabel?: string }

const ConfirmCtx = createContext<(opts: ConfirmOpts) => Promise<boolean>>(async () => false)

export function useConfirm() {
  return useContext(ConfirmCtx)
}

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [opts, setOpts] = useState<ConfirmOpts | null>(null)
  const resolver = useRef<(v: boolean) => void>()

  const confirm = useCallback((o: ConfirmOpts) => {
    setOpts(o)
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve
    })
  }, [])

  const close = (v: boolean) => {
    resolver.current?.(v)
    setOpts(null)
  }

  return (
    <ConfirmCtx.Provider value={confirm}>
      {children}
      <AnimatePresence>
        {opts && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[90] grid place-items-center bg-bg/70 p-4 backdrop-blur-sm"
            onClick={() => close(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 18, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.97 }}
              transition={{ type: 'spring', bounce: 0.22, duration: 0.4 }}
              className="w-full max-w-sm rounded-2xl border border-border glass-card p-5 shadow-card"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-3 flex items-center gap-2.5">
                <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-danger/15 text-danger">
                  <TriangleAlert className="size-4.5" />
                </span>
                <h3 className="text-base font-semibold">{opts.title}</h3>
              </div>
              {opts.body && <p className="mb-4 text-sm leading-relaxed text-muted">{opts.body}</p>}
              <div className="flex justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={() => close(false)}>إلغاء</Button>
                <Button variant="danger" size="sm" onClick={() => close(true)}>
                  {opts.confirmLabel || 'تأكيد الحذف'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </ConfirmCtx.Provider>
  )
}
