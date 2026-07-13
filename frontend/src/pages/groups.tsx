import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Users2, Plus, Loader2, X, Ban, Trash2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TextField, inputCls } from '@/components/ui/field'
import { useToast } from '@/components/ui/toast'
import { api, type Group, type BlockedWord } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { cn, timeAgo } from '@/lib/utils'

export function GroupsPage() {
  const { data: groups, loading, refresh } = useData(() => api.groups())
  const toast = useToast()
  const [gid, setGid] = useState('')
  const [gname, setGname] = useState('')
  const [busy, setBusy] = useState(false)
  const [wordsGroup, setWordsGroup] = useState<Group | null>(null)

  const addGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    try {
      const r = await api.addGroup(gid, gname)
      toast('success', r.message)
      setGid(''); setGname('')
      refresh(true)
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الإضافة')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {loading ? (
        <PageSpinner />
      ) : !groups?.length ? (
        <EmptyState icon={<Users2 className="size-8" />} text="لا توجد مجموعات مُدارة بعد — أضف البوت لمجموعة أو سجّلها يدوياً" />
      ) : (
        <div className="grid gap-3">
          {groups.map((g, i) => (
            <motion.div
              key={g.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="flex flex-wrap items-center gap-4 p-4">
                <span className={cn(
                  'grid size-11 shrink-0 place-items-center rounded-xl ring-1',
                  g.is_active
                    ? 'bg-success/10 text-success ring-success/25'
                    : 'bg-bg/60 text-muted ring-border'
                )}>
                  <Users2 className="size-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{g.name}</p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-muted">
                    <span dir="ltr" className="font-mono">{g.telegram_group_id}</span>
                    <span>{g.is_active ? '🟢 نشطة' : '⚪️ غير نشطة'}</span>
                    <span>{timeAgo(g.activated_at)}</span>
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => setWordsGroup(g)}>
                  <Ban className="size-3.5" />
                  الكلمات المحظورة
                </Button>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <Card className="p-5">
        <h2 className="mb-4 text-sm font-semibold">➕ تسجيل مجموعة يدوياً</h2>
        <form onSubmit={addGroup} className="grid gap-x-4 sm:grid-cols-2">
          <TextField
            label="معرّف المجموعة (Telegram ID)"
            placeholder="-100123456789"
            dir="ltr"
            value={gid}
            onChange={(e) => setGid(e.target.value)}
            required
          />
          <TextField
            label="اسم المجموعة"
            placeholder="مجموعة القهوة المختصة"
            value={gname}
            onChange={(e) => setGname(e.target.value)}
            required
          />
          <div className="sm:col-span-2">
            <Button type="submit" size="sm" disabled={busy || !gid || !gname}>
              {busy ? <Loader2 className="animate-spin" /> : <Plus />}
              تسجيل المجموعة
            </Button>
          </div>
        </form>
      </Card>

      <AnimatePresence>
        {wordsGroup && (
          <WordsDrawer group={wordsGroup} onClose={() => setWordsGroup(null)} />
        )}
      </AnimatePresence>
    </div>
  )
}

function WordsDrawer({ group, onClose }: { group: Group; onClose: () => void }) {
  const { data, refresh } = useData(() => api.groupWords(group.id))
  const toast = useToast()
  const [word, setWord] = useState('')
  const [busy, setBusy] = useState(false)

  const add = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!word.trim() || busy) return
    setBusy(true)
    try {
      const r = await api.addGroupWord(group.id, word.trim())
      toast('success', r.message)
      setWord('')
      refresh(true)
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الإضافة')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (w: BlockedWord) => {
    try {
      await api.deleteGroupWord(group.id, w.id)
      refresh(true)
    } catch {
      toast('error', 'فشل الحذف')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[80] bg-bg/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.aside
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', bounce: 0.1, duration: 0.45 }}
        className="absolute inset-y-0 start-0 flex w-[min(92vw,26rem)] flex-col border-e border-border glass-card"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold">🚫 الكلمات المحظورة</h2>
            <p className="truncate text-xs text-muted">{group.name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid size-8 shrink-0 place-items-center rounded-lg text-muted hover:bg-bg-elev hover:text-ink"
          >
            <X className="size-4" />
          </button>
        </header>

        <form onSubmit={add} className="flex gap-2 border-b border-border px-5 py-4">
          <input
            className={inputCls}
            placeholder="أضف كلمة…"
            value={word}
            onChange={(e) => setWord(e.target.value)}
          />
          <Button type="submit" size="sm" disabled={busy || !word.trim()}>
            {busy ? <Loader2 className="animate-spin" /> : <Plus />}
          </Button>
        </form>

        <div className="flex-1 overflow-y-auto p-5">
          {!data ? (
            <PageSpinner />
          ) : !data.words.length ? (
            <p className="pt-8 text-center text-sm text-muted">لا توجد كلمات محظورة لهذه المجموعة</p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              <AnimatePresence initial={false}>
                {data.words.map((w) => (
                  <motion.li
                    key={w.id}
                    layout
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.85 }}
                    className="flex items-center gap-1.5 rounded-full border border-border bg-bg/60 py-1.5 pe-2 ps-3.5 text-sm"
                  >
                    <span>{w.word}</span>
                    <button
                      type="button"
                      onClick={() => remove(w)}
                      className="grid size-5 place-items-center rounded-full text-muted hover:bg-danger/15 hover:text-danger"
                    >
                      <Trash2 className="size-3" />
                    </button>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          )}
        </div>
      </motion.aside>
    </motion.div>
  )
}

export function PageSpinner() {
  return (
    <div className="grid place-items-center py-16 text-muted">
      <Loader2 className="size-6 animate-spin" />
    </div>
  )
}

export function EmptyState({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <Card className="grid place-items-center gap-3 p-10 text-center">
      <span className="grid size-14 place-items-center rounded-2xl bg-bg/60 text-muted">{icon}</span>
      <p className="max-w-md text-sm leading-relaxed text-muted">{text}</p>
    </Card>
  )
}
