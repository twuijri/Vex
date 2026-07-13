import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LineChart, Trash2, CircleCheck, CircleAlert, Clock, ChevronDown } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { api, type StatRow } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { cn } from '@/lib/utils'
import { PageSpinner, EmptyState } from '@/pages/groups'

function ErrorLine({ text }: { text: string }) {
  const [open, setOpen] = useState(false)
  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      className="mt-2.5 flex w-full items-start gap-2 rounded-lg bg-danger/5 px-3 py-1.5 text-start ring-1 ring-danger/15 transition-colors hover:bg-danger/10"
      title={open ? 'اضغط للطي' : 'اضغط لعرض الخطأ كاملاً'}
    >
      <ChevronDown className={cn('mt-0.5 size-3 shrink-0 text-danger/70 transition-transform', open && 'rotate-180')} />
      <span
        dir="ltr"
        className={cn(
          'min-w-0 flex-1 text-start font-mono text-[11px] leading-relaxed text-danger/90',
          open ? 'whitespace-pre-wrap break-all' : 'truncate'
        )}
      >
        {text}
      </span>
    </button>
  )
}

const STATUS_META: Record<string, { label: string; cls: string; icon: typeof CircleCheck }> = {
  ok: { label: 'سليم', cls: 'text-success bg-success/10 ring-success/25', icon: CircleCheck },
  error: { label: 'خطأ', cls: 'text-danger bg-danger/10 ring-danger/25', icon: CircleAlert },
  rate_limit_minute: { label: 'حد الدقيقة', cls: 'text-warning bg-warning/10 ring-warning/25', icon: Clock },
  rate_limit_day: { label: 'حد اليوم', cls: 'text-warning bg-warning/10 ring-warning/25', icon: Clock },
}

export function StatsPage() {
  // Auto-refresh every 15s — the "live" feel
  const { data, loading, refresh } = useData(() => api.aiStats(30), 15_000)
  const toast = useToast()

  const remove = async (row: StatRow) => {
    try {
      await api.deleteAiStat(row.id)
      refresh(true)
    } catch {
      toast('error', 'فشل الحذف')
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {loading && !data ? (
        <PageSpinner />
      ) : !data?.stats.length ? (
        <EmptyState icon={<LineChart className="size-8" />} text="لا توجد إحصائيات بعد — ستظهر هنا أول ما يبدأ التحليل" />
      ) : (
        <>
          {/* Summaries */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {data.summaries.map((s, i) => (
              <motion.div
                key={s.label}
                className="min-w-0"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card className="overflow-hidden p-4">
                  <p className="truncate text-xs text-muted" dir="ltr">{s.label}</p>
                  <p className="mt-2 text-2xl font-bold tabular-nums">{s.today.toLocaleString('en')}</p>
                  <p className="mt-0.5 text-[11px] text-muted">
                    اليوم · {s.total.toLocaleString('en')} إجمالاً (٣٠ يوم)
                  </p>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Detail rows */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">📋 سجل الطلبات التفصيلي</h2>
              <span className="flex items-center gap-1.5 text-[11px] text-muted">
                <span className="size-1.5 animate-pulse-soft rounded-full bg-success" />
                يتحدث تلقائياً كل ١٥ ثانية
              </span>
            </div>
            <div className="grid gap-2.5">
              <AnimatePresence initial={false}>
                {data.stats.map((row) => {
                  const meta = STATUS_META[row.status] || { label: row.status, cls: 'text-muted bg-bg/60 ring-border', icon: CircleAlert }
                  const Icon = meta.icon
                  return (
                    <motion.div
                      key={row.id}
                      layout
                      className="min-w-0"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.97 }}
                    >
                      <Card className="overflow-hidden p-4">
                        <div className="flex flex-wrap items-center gap-3">
                          <span className={cn('inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1', meta.cls)}>
                            <Icon className="size-3.5" />
                            {meta.label}
                          </span>
                          <span className="min-w-0 flex-1 truncate font-mono text-xs font-semibold" dir="ltr">
                            {row.provider}
                          </span>
                          <span className="shrink-0 rounded-lg bg-bg/60 px-2 py-1 text-[11px] text-muted tabular-nums ring-1 ring-border">
                            {row.requests} طلب
                          </span>
                          <span className="shrink-0 text-[11px] text-muted tabular-nums" dir="ltr">
                            {row.date} · {row.last_used}
                          </span>
                          <button
                            type="button"
                            onClick={() => remove(row)}
                            className="grid size-7 shrink-0 place-items-center rounded-lg text-muted hover:bg-danger/15 hover:text-danger"
                            title="حذف السجل"
                          >
                            <Trash2 className="size-3.5" />
                          </button>
                        </div>
                        {row.error && <ErrorLine text={row.error} />}
                        {!row.error && row.raw_response && (
                          <p className="mt-2.5 truncate rounded-lg bg-bg/50 px-3 py-1.5 font-mono text-[11px] text-muted ring-1 ring-border" dir="ltr">
                            ↳ {row.raw_response}
                          </p>
                        )}
                      </Card>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
