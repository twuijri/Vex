import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2, Lock, RotateCcw, Save, Radio, BellRing, Trash } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TextField } from '@/components/ui/field'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { PageSpinner } from '@/pages/groups'

export function PromptPage() {
  const { data, loading, refresh } = useData(() => api.prompt())
  const toast = useToast()

  if (loading || !data) return <PageSpinner />

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {!data.has_providers && (
        <Card className="border-warning/40 bg-warning/5 p-4 text-sm text-warning">
          ⚠️ لا توجد موديلات مفعّلة — أضف مزوداً وموديلاً من صفحة المزودين ليعمل التحليل
        </Card>
      )}
      <RulesEditor
        fixedPrefix={data.fixed_prefix}
        fixedSuffix={data.fixed_suffix}
        initial={data.current_rules}
        defaultRules={data.default_rules}
        onSaved={() => refresh(true)}
      />
      <ThresholdsCard
        alert={data.alert_threshold}
        autoDelete={data.auto_delete_threshold}
        onSaved={() => refresh(true)}
      />
      <DebugChannelCard channelId={data.debug_channel_id} onSaved={() => refresh(true)} />
    </div>
  )
}

function RulesEditor({
  fixedPrefix, fixedSuffix, initial, defaultRules, onSaved,
}: {
  fixedPrefix: string
  fixedSuffix: string
  initial: string
  defaultRules: string
  onSaved: () => void
}) {
  const toast = useToast()
  const [rules, setRules] = useState(initial)
  const [busy, setBusy] = useState(false)

  useEffect(() => setRules(initial), [initial])

  const save = async () => {
    setBusy(true)
    try {
      const r = await api.savePrompt(rules)
      toast('success', r.message)
      onSaved()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الحفظ')
    } finally {
      setBusy(false)
    }
  }

  const reset = async () => {
    setBusy(true)
    try {
      const r = await api.resetPrompt()
      toast('success', r.message)
      onSaved()
    } catch {
      toast('error', 'فشل إعادة الضبط')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="p-5">
      <h2 className="text-sm font-semibold">📝 قواعد المجموعة</h2>
      <p className="mt-1 text-xs leading-relaxed text-muted">
        اكتب فقط <strong className="text-ink">ما تريد منعه</strong> — الجزء المقفل بالأعلى والأسفل يُضاف تلقائياً
      </p>

      <div className="mt-4 overflow-hidden rounded-xl border border-border">
        <div className="flex items-start gap-2 bg-bg/70 px-4 py-3 text-xs leading-relaxed text-muted">
          <Lock className="mt-0.5 size-3.5 shrink-0" />
          <pre className="whitespace-pre-wrap font-sans">{fixedPrefix}</pre>
        </div>
        <textarea
          className="block min-h-40 w-full resize-y border-y border-border bg-transparent px-4 py-3 text-sm leading-relaxed outline-none placeholder:text-muted/50 focus:bg-accent/[0.03]"
          value={rules}
          onChange={(e) => setRules(e.target.value)}
          placeholder={defaultRules}
        />
        <div className="flex items-start gap-2 bg-bg/70 px-4 py-3 text-xs leading-relaxed text-muted">
          <Lock className="mt-0.5 size-3.5 shrink-0" />
          <pre className="whitespace-pre-wrap font-sans">{fixedSuffix}</pre>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button size="sm" onClick={save} disabled={busy}>
          {busy ? <Loader2 className="animate-spin" /> : <Save />}
          حفظ القواعد
        </Button>
        <Button size="sm" variant="danger" onClick={reset} disabled={busy}>
          <RotateCcw />
          إعادة الضبط
        </Button>
        <span className="text-xs text-muted">إذا تركت الحقل فارغاً تُستخدم القواعد الافتراضية</span>
      </div>
    </Card>
  )
}

function ThresholdsCard({
  alert, autoDelete, onSaved,
}: { alert: number; autoDelete: number; onSaved: () => void }) {
  const toast = useToast()
  const [alertV, setAlertV] = useState(Math.round(alert * 100))
  const [deleteV, setDeleteV] = useState(Math.round(autoDelete * 100))
  const [busy, setBusy] = useState(false)

  useEffect(() => { setAlertV(Math.round(alert * 100)); setDeleteV(Math.round(autoDelete * 100)) }, [alert, autoDelete])

  const save = async () => {
    setBusy(true)
    try {
      const r = await api.saveThresholds(alertV / 100, deleteV / 100)
      toast('success', r.message)
      onSaved()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الحفظ')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="p-5">
      <h2 className="text-sm font-semibold">⚡ عتبات الإجراء</h2>
      <p className="mt-1 text-xs text-muted">تحكم متى يُنبَّه المشرفون ومتى تُحذف الرسالة تلقائياً</p>

      <div className="mt-5 space-y-6">
        <SliderRow
          icon={<BellRing className="size-4 text-warning" />}
          label="تنبيه المشرفين إذا تجاوزت"
          value={alertV}
          onChange={setAlertV}
          tone="warning"
        />
        <SliderRow
          icon={<Trash className="size-4 text-danger" />}
          label="حذف تلقائي إذا تجاوزت"
          value={deleteV}
          onChange={setDeleteV}
          tone="danger"
        />
      </div>

      {alertV >= deleteV && (
        <p className="mt-4 rounded-xl border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-danger">
          عتبة التنبيه يجب أن تكون أقل من عتبة الحذف التلقائي
        </p>
      )}

      <Button size="sm" className="mt-4" onClick={save} disabled={busy || alertV >= deleteV}>
        {busy ? <Loader2 className="animate-spin" /> : <Save />}
        حفظ العتبات
      </Button>
    </Card>
  )
}

function SliderRow({
  icon, label, value, onChange, tone,
}: {
  icon: React.ReactNode
  label: string
  value: number
  onChange: (v: number) => void
  tone: 'warning' | 'danger'
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 font-medium">{icon}{label}</span>
        <motion.span
          key={value}
          initial={{ scale: 1.25 }}
          animate={{ scale: 1 }}
          className={`font-bold tabular-nums ${tone === 'warning' ? 'text-warning' : 'text-danger'}`}
        >
          {value}%
        </motion.span>
      </div>
      <input
        type="range"
        min={5}
        max={95}
        step={5}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[hsl(var(--accent))]"
      />
      <div className="mt-1 flex justify-between text-[10px] text-muted">
        <span>5%</span><span>50%</span><span>95%</span>
      </div>
    </div>
  )
}

function DebugChannelCard({ channelId, onSaved }: { channelId: number | null; onSaved: () => void }) {
  const toast = useToast()
  const [value, setValue] = useState(channelId ? String(channelId) : '')
  const [busy, setBusy] = useState(false)

  useEffect(() => setValue(channelId ? String(channelId) : ''), [channelId])

  const save = async (v: string) => {
    setBusy(true)
    try {
      const r = await api.saveDebugChannel(v)
      toast('success', r.message)
      onSaved()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الحفظ')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="p-5">
      <h2 className="flex items-center gap-2 text-sm font-semibold">
        <Radio className="size-4 text-accent-from" />
        قناة التتبع (Debug)
      </h2>
      <p className="mt-1 text-xs text-muted">
        إذا فُعّلت، يرسل البوت نتيجة تحليل كل رسالة لهذه القناة
        {channelId ? ' — مفعّلة حالياً' : ' — متوقفة حالياً'}
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-2">
        <div className="min-w-52 flex-1">
          <TextField
            label="معرّف القناة"
            placeholder="-100123456789"
            dir="ltr"
            className="mb-0 font-mono"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </div>
        <Button size="sm" onClick={() => save(value)} disabled={busy || !value.trim()}>
          {busy ? <Loader2 className="animate-spin" /> : <Save />}
          حفظ
        </Button>
        {channelId && (
          <Button size="sm" variant="danger" onClick={() => save('')} disabled={busy}>
            إيقاف
          </Button>
        )}
      </div>
    </Card>
  )
}
