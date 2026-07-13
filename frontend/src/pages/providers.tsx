import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  DndContext, closestCenter, PointerSensor, useSensor, useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext, arrayMove, verticalListSortingStrategy, useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  Bot, Plug, Plus, Loader2, Trash2, Pencil, GripVertical, RefreshCw, Search,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TextField, SecretField, Select, Toggle, Label, inputCls } from '@/components/ui/field'
import { useToast } from '@/components/ui/toast'
import { useConfirm } from '@/components/ui/confirm'
import { api, type Endpoint, type AIModel } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { cn } from '@/lib/utils'
import { PageSpinner, EmptyState } from '@/pages/groups'

const TYPE_META: Record<string, { label: string; dot: string }> = {
  litellm: { label: 'LiteLLM / OpenAI-compatible', dot: 'bg-warning' },
  google_studio: { label: 'Google AI Studio', dot: 'bg-sky-400' },
  blackbox: { label: 'Blackbox.ai', dot: 'bg-purple-400' },
  huggingface: { label: 'HuggingFace', dot: 'bg-orange-400' },
}

export function ProvidersPage() {
  const endpoints = useData(() => api.endpoints())
  const models = useData(() => api.models())

  return (
    <div className="mx-auto max-w-5xl space-y-10">
      <EndpointsSection
        endpoints={endpoints.data}
        loading={endpoints.loading}
        refresh={() => { endpoints.refresh(true); models.refresh(true) }}
      />
      <ModelsSection
        models={models.data}
        endpoints={endpoints.data}
        loading={models.loading}
        refresh={() => { models.refresh(true); endpoints.refresh(true) }}
      />
    </div>
  )
}

/* ═══════════════ Endpoints (saved connections) ═══════════════ */

function EndpointsSection({
  endpoints, loading, refresh,
}: { endpoints: Endpoint[] | null; loading: boolean; refresh: () => void }) {
  const toast = useToast()
  const confirm = useConfirm()
  const [editing, setEditing] = useState<Endpoint | null>(null)
  const [showAdd, setShowAdd] = useState(false)

  const remove = async (ep: Endpoint) => {
    const ok = await confirm({
      title: `حذف المزود «${ep.name}»؟`,
      body: ep.model_count
        ? `سيتم حذف ${ep.model_count} موديل مرتبط به من سلسلة التحليل.`
        : 'لا توجد موديلات مرتبطة به.',
    })
    if (!ok) return
    try {
      await api.deleteEndpoint(ep.id)
      toast('success', 'تم حذف المزود')
      refresh()
    } catch {
      toast('error', 'فشل الحذف')
    }
  }

  return (
    <section>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Plug className="size-4 text-accent-from" />
            المزودون المحفوظون
          </h2>
          <p className="mt-0.5 text-xs text-muted">الرابط والمفتاح يُحفظان مرة واحدة — الموديلات تُضاف منها</p>
        </div>
        <Button size="sm" variant={showAdd ? 'secondary' : 'primary'} onClick={() => setShowAdd((v) => !v)}>
          <Plus />
          مزود جديد
        </Button>
      </div>

      <AnimatePresence initial={false}>
        {showAdd && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <AddEndpointForm
              onDone={() => { setShowAdd(false); refresh() }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <PageSpinner />
      ) : !endpoints?.length ? (
        !showAdd && <EmptyState icon={<Plug className="size-8" />} text="لا يوجد مزودون محفوظون — أضف أول مزود وسيبقى محفوظاً حتى لو حذفت موديلاته" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {endpoints.map((ep) => {
            const meta = TYPE_META[ep.provider_type] || { label: ep.provider_type, dot: 'bg-muted' }
            return (
              <Card key={ep.id} className="p-4">
                <div className="flex items-start gap-3">
                  <span className="mt-1 grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 text-accent-from ring-1 ring-accent/20">
                    <Plug className="size-4.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2 text-sm font-semibold">
                      <span className="truncate">{ep.name}</span>
                      <span className="shrink-0 rounded-full bg-bg/70 px-2 py-0.5 text-[10px] font-medium text-muted ring-1 ring-border">
                        {ep.model_count} موديل
                      </span>
                    </p>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
                      <span className={cn('size-1.5 rounded-full', meta.dot)} />
                      {meta.label}
                    </p>
                    {(ep.base_url || ep.key_hint) && (
                      <p className="mt-1 truncate font-mono text-[11px] text-muted/80" dir="ltr">
                        {ep.base_url || ''}{ep.base_url && ep.key_hint ? ' · ' : ''}{ep.key_hint ? `🔑 ${ep.key_hint}` : ''}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <button
                      type="button"
                      onClick={() => setEditing(ep)}
                      className="grid size-8 place-items-center rounded-lg text-muted hover:bg-bg-elev hover:text-ink"
                      title="تعديل"
                    >
                      <Pencil className="size-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(ep)}
                      className="grid size-8 place-items-center rounded-lg text-muted hover:bg-danger/15 hover:text-danger"
                      title="حذف"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <AnimatePresence>
        {editing && (
          <EditEndpointModal
            endpoint={editing}
            onClose={() => setEditing(null)}
            onSaved={() => { setEditing(null); refresh() }}
          />
        )}
      </AnimatePresence>
    </section>
  )
}

function AddEndpointForm({ onDone }: { onDone: () => void }) {
  const toast = useToast()
  const [name, setName] = useState('')
  const [type, setType] = useState('litellm')
  const [baseUrl, setBaseUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [busy, setBusy] = useState(false)
  const isLitellm = type === 'litellm'

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    try {
      await api.addEndpoint({ name, provider_type: type, api_key: apiKey, base_url: baseUrl })
      toast('success', 'تم حفظ المزود')
      onDone()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الحفظ')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="mb-4 border-accent/25 p-5">
      <form onSubmit={submit} className="grid gap-x-4 sm:grid-cols-2">
        <TextField
          label="الاسم (للتعريف فقط)"
          placeholder="مثال: LiteLLM VPS / Ollama Cloud"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Select label="نوع المزود" value={type} onChange={(e) => setType(e.target.value)}>
          {Object.entries(TYPE_META).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </Select>
        {isLitellm && (
          <TextField
            label="رابط السيرفر (Base URL)"
            placeholder="http://192.168.1.10:4000"
            dir="ltr"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            hint="يُضاف /v1 تلقائياً"
          />
        )}
        <SecretField
          label={isLitellm ? 'Virtual Key (اختياري)' : 'مفتاح API'}
          placeholder="sk-…"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          required={!isLitellm}
        />
        <div className="sm:col-span-2">
          <Button type="submit" size="sm" disabled={busy || !name}>
            {busy ? <Loader2 className="animate-spin" /> : <Plus />}
            حفظ المزود
          </Button>
        </div>
      </form>
    </Card>
  )
}

function EditEndpointModal({
  endpoint, onClose, onSaved,
}: { endpoint: Endpoint; onClose: () => void; onSaved: () => void }) {
  const toast = useToast()
  const [name, setName] = useState(endpoint.name)
  const [baseUrl, setBaseUrl] = useState(endpoint.base_url || '')
  const [apiKey, setApiKey] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    try {
      await api.updateEndpoint(endpoint.id, { name, api_key: apiKey, base_url: baseUrl })
      toast('success', 'تم تحديث المزود — كل الموديلات المرتبطة تستخدم البيانات الجديدة')
      onSaved()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل التحديث')
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[85] grid place-items-center bg-bg/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: 18, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.97 }}
        transition={{ type: 'spring', bounce: 0.22, duration: 0.4 }}
        className="w-full max-w-md rounded-2xl border border-border glass-card p-5 shadow-card"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-4 text-base font-semibold">✏️ تعديل «{endpoint.name}»</h3>
        <form onSubmit={submit}>
          <TextField label="الاسم" value={name} onChange={(e) => setName(e.target.value)} />
          {endpoint.provider_type === 'litellm' && (
            <TextField
              label="رابط السيرفر (Base URL)"
              dir="ltr"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          )}
          <SecretField
            label="مفتاح جديد"
            placeholder="اتركه فارغاً للإبقاء على المفتاح الحالي"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            hint={endpoint.key_hint ? `المفتاح الحالي: ${endpoint.key_hint}` : undefined}
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>إلغاء</Button>
            <Button type="submit" size="sm" disabled={busy}>
              {busy ? <Loader2 className="animate-spin" /> : null}
              حفظ التعديلات
            </Button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}

/* ═══════════════ Models (cascade, drag & drop) ═══════════════ */

function ModelsSection({
  models, endpoints, loading, refresh,
}: {
  models: AIModel[] | null
  endpoints: Endpoint[] | null
  loading: boolean
  refresh: () => void
}) {
  const toast = useToast()
  const confirm = useConfirm()
  const [order, setOrder] = useState<number[] | null>(null)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))

  const list = useMemo(() => {
    if (!models) return []
    if (!order) return models
    const byId = new Map(models.map((m) => [m.id, m]))
    return order.map((id) => byId.get(id)).filter(Boolean) as AIModel[]
  }, [models, order])

  const onDragEnd = async (ev: DragEndEvent) => {
    const { active, over } = ev
    if (!over || active.id === over.id || !models) return
    const ids = (order ?? models.map((m) => m.id))
    const from = ids.indexOf(Number(active.id))
    const to = ids.indexOf(Number(over.id))
    const next = arrayMove(ids, from, to)
    setOrder(next)
    try {
      await api.reorderModels(next)
      toast('success', 'تم تحديث ترتيب السلسلة')
      refresh()
    } catch {
      toast('error', 'فشل حفظ الترتيب')
      setOrder(null)
    }
  }

  const toggle = async (m: AIModel) => {
    try {
      await api.toggleModel(m.id)
      refresh()
    } catch {
      toast('error', 'فشل التبديل')
    }
  }

  const remove = async (m: AIModel) => {
    const ok = await confirm({
      title: `حذف الموديل «${m.name}»؟`,
      body: 'المزود المرتبط به يبقى محفوظاً ويمكنك إعادة إضافة الموديل منه في أي وقت.',
    })
    if (!ok) return
    try {
      await api.deleteModel(m.id)
      setOrder(null)
      toast('success', 'تم حذف الموديل')
      refresh()
    } catch {
      toast('error', 'فشل الحذف')
    }
  }

  return (
    <section>
      <div className="mb-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Bot className="size-4 text-accent-from" />
          الموديلات — سلسلة التحليل
        </h2>
        <p className="mt-0.5 text-xs text-muted">
          اسحب الموديلات لإعادة ترتيبها — تُجرَّب بالترتيب وإذا فشل أحدها انتقل للتالي تلقائياً
        </p>
      </div>

      {loading ? (
        <PageSpinner />
      ) : !list.length ? (
        <EmptyState icon={<Bot className="size-8" />} text="لا توجد موديلات في السلسلة — أضف أول موديل من النموذج أدناه" />
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={list.map((m) => m.id)} strategy={verticalListSortingStrategy}>
            <div className="grid gap-2.5">
              {list.map((m, i) => (
                <SortableModelCard
                  key={m.id}
                  model={m}
                  index={i}
                  onToggle={() => toggle(m)}
                  onDelete={() => remove(m)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      <AddModelForm endpoints={endpoints || []} onAdded={() => { setOrder(null); refresh() }} />
    </section>
  )
}

function SortableModelCard({
  model, index, onToggle, onDelete,
}: { model: AIModel; index: number; onToggle: () => void; onDelete: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: model.id })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(isDragging && 'z-10')}
    >
      <Card className={cn(
        'flex items-center gap-3 p-3.5',
        isDragging && 'border-accent/50 shadow-glow',
        !model.is_active && 'opacity-55'
      )}>
        <button
          type="button"
          className="grid size-8 shrink-0 cursor-grab touch-none place-items-center rounded-lg text-muted hover:bg-bg-elev hover:text-ink active:cursor-grabbing"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" />
        </button>
        <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-accent/25 to-accent/5 text-xs font-bold text-accent-from ring-1 ring-accent/25 tabular-nums">
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{model.name}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2.5 text-[11px] text-muted">
            {model.endpoint_name && (
              <span className="inline-flex items-center gap-1">
                <Plug className="size-3" />
                {model.endpoint_name}
              </span>
            )}
            <span className="font-mono" dir="ltr">{model.model}</span>
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Toggle checked={model.is_active} onChange={onToggle} />
          <button
            type="button"
            onClick={onDelete}
            className="grid size-8 place-items-center rounded-lg text-muted hover:bg-danger/15 hover:text-danger"
            title="حذف"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </Card>
    </div>
  )
}

function AddModelForm({ endpoints, onAdded }: { endpoints: Endpoint[]; onAdded: () => void }) {
  const toast = useToast()
  const [endpointId, setEndpointId] = useState<string>('')
  const [model, setModel] = useState('')
  const [name, setName] = useState('')
  const [available, setAvailable] = useState<string[]>([])
  const [fetching, setFetching] = useState(false)
  const [busy, setBusy] = useState(false)
  const [filter, setFilter] = useState('')

  const epId = endpointId ? Number(endpointId) : endpoints[0]?.id
  const shown = filter
    ? available.filter((m) => m.toLowerCase().includes(filter.toLowerCase()))
    : available

  const fetchModels = async () => {
    if (!epId || fetching) return
    setFetching(true)
    setAvailable([])
    try {
      const r = await api.fetchEndpointModels(epId)
      if (r.error && !r.models.length) toast('error', r.error)
      setAvailable(r.models)
      if (r.models.length) toast('success', `وُجد ${r.models.length} موديل`)
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الجلب')
    } finally {
      setFetching(false)
    }
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy || !epId || !model.trim()) return
    setBusy(true)
    try {
      await api.addModel({ endpoint_id: epId, model: model.trim(), name: name.trim() })
      toast('success', 'تمت إضافة الموديل لنهاية السلسلة')
      setModel(''); setName(''); setFilter('')
      onAdded()
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'فشل الإضافة')
    } finally {
      setBusy(false)
    }
  }

  if (!endpoints.length) return null

  return (
    <Card className="mt-4 p-5">
      <h3 className="mb-4 text-sm font-semibold">➕ إضافة موديل جديد</h3>
      <form onSubmit={submit}>
        <div className="grid gap-x-4 sm:grid-cols-2">
          <Select
            label="المزود"
            value={endpointId || String(endpoints[0]?.id ?? '')}
            onChange={(e) => { setEndpointId(e.target.value); setAvailable([]); setFilter('') }}
          >
            {endpoints.map((ep) => (
              <option key={ep.id} value={ep.id}>{ep.name}</option>
            ))}
          </Select>
          <TextField
            label="الاسم (اختياري)"
            placeholder="الافتراضي: اسم الموديل"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <Label>الموديل</Label>
          <div className="flex gap-2">
            <input
              className={inputCls}
              dir="ltr"
              placeholder="gpt-4o أو اضغط جلب الموديلات →"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required
            />
            <Button type="button" variant="secondary" size="sm" className="h-auto shrink-0" onClick={fetchModels} disabled={fetching}>
              {fetching ? <Loader2 className="animate-spin" /> : <RefreshCw />}
              جلب الموديلات
            </Button>
          </div>

          <AnimatePresence>
            {available.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-2 rounded-xl border border-border bg-bg/50">
                  <div className="flex items-center gap-2 border-b border-border px-3 py-2">
                    <Search className="size-3.5 text-muted" />
                    <input
                      className="w-full bg-transparent text-xs outline-none placeholder:text-muted/60"
                      placeholder="فلترة…"
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                    />
                    <span className="shrink-0 text-[10px] text-muted tabular-nums">{shown.length}</span>
                  </div>
                  <div className="grid max-h-44 grid-cols-1 gap-1 overflow-y-auto p-2 sm:grid-cols-2">
                    {shown.map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setModel(m)}
                        className={cn(
                          'truncate rounded-lg px-2.5 py-1.5 text-start font-mono text-xs transition-colors',
                          model === m
                            ? 'bg-accent/15 text-accent-from ring-1 ring-accent/30'
                            : 'text-muted hover:bg-bg-elev hover:text-ink'
                        )}
                        dir="ltr"
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <Button type="submit" size="sm" disabled={busy || !model.trim()}>
          {busy ? <Loader2 className="animate-spin" /> : <Plus />}
          إضافة الموديل
        </Button>
      </form>
    </Card>
  )
}
