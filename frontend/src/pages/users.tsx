import { motion } from 'framer-motion'
import { UserX } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { timeAgo } from '@/lib/utils'
import { PageSpinner, EmptyState } from '@/pages/groups'

export function UsersPage() {
  const { data: users, loading } = useData(() => api.blockedUsers())

  return (
    <div className="mx-auto max-w-5xl">
      {loading ? (
        <PageSpinner />
      ) : !users?.length ? (
        <EmptyState icon={<UserX className="size-8" />} text="لا يوجد مستخدمون محظورون 🎉" />
      ) : (
        <div className="grid gap-3">
          {users.map((u, i) => (
            <motion.div
              key={u.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="flex items-center gap-4 p-4">
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-danger/10 text-danger ring-1 ring-danger/25">
                  <UserX className="size-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">
                    {u.first_name} {u.last_name || ''}
                  </p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-muted">
                    {u.username && <span dir="ltr">@{u.username}</span>}
                    <span dir="ltr" className="font-mono">{u.telegram_id}</span>
                  </p>
                </div>
                <span className="shrink-0 text-xs text-muted">حُظر {timeAgo(u.blocked_at)}</span>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
