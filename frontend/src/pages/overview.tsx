import { motion } from 'framer-motion'
import { Users, UserX, Users2, ShieldCheck, ArrowLeft, Bot, LineChart, PencilRuler } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { navigate } from '@/lib/router'

const STATS = [
  { key: 'users' as const, label: 'المستخدمون', icon: Users, tint: 'text-accent-from' },
  { key: 'groups' as const, label: 'المجموعات المُدارة', icon: Users2, tint: 'text-success' },
  { key: 'blocked' as const, label: 'المحظورون', icon: UserX, tint: 'text-danger' },
  { key: 'admins' as const, label: 'المشرفون', icon: ShieldCheck, tint: 'text-warning' },
]

const LINKS = [
  { path: '/providers', label: 'المزودون والموديلات', sub: 'إدارة اتصالات الذكاء الاصطناعي', icon: Bot },
  { path: '/stats', label: 'إحصائيات الذكاء الاصطناعي', sub: 'الطلبات والأخطاء لحظياً', icon: LineChart },
  { path: '/prompt', label: 'محرر البرومبت', sub: 'قواعد المجموعة وعتبات الإجراء', icon: PencilRuler },
]

export function OverviewPage() {
  const { data, loading } = useData(() => api.overview(), 30_000)

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {STATS.map((s, i) => {
          const Icon = s.icon
          return (
            <motion.div
              key={s.key}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, type: 'spring', bounce: 0.25, duration: 0.55 }}
            >
              <Card className="p-5">
                <div className="flex items-center justify-between">
                  <span className={`grid size-10 place-items-center rounded-xl bg-bg/60 ${s.tint}`}>
                    <Icon className="size-5" strokeWidth={2.2} />
                  </span>
                </div>
                <p className="mt-4 text-3xl font-bold tabular-nums tracking-tight">
                  {loading || !data ? '—' : data[s.key].toLocaleString('en')}
                </p>
                <p className="mt-1 text-sm text-muted">{s.label}</p>
              </Card>
            </motion.div>
          )
        })}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-muted">وصول سريع</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {LINKS.map((l, i) => {
            const Icon = l.icon
            return (
              <motion.button
                key={l.path}
                type="button"
                onClick={() => navigate(l.path)}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 + i * 0.07, type: 'spring', bounce: 0.25, duration: 0.55 }}
                className="group text-start"
              >
                <Card className="flex items-center gap-4 p-5 transition-all group-hover:-translate-y-1 group-hover:border-accent/40">
                  <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 text-accent-from ring-1 ring-accent/20">
                    <Icon className="size-5" strokeWidth={2.2} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold">{l.label}</span>
                    <span className="block truncate text-xs text-muted">{l.sub}</span>
                  </span>
                  <ArrowLeft className="size-4 shrink-0 text-muted transition-transform group-hover:-translate-x-1 group-hover:text-accent-from rtl-flip" />
                </Card>
              </motion.button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
