import { useEffect, useRef, useState } from 'react'
import { ScrollText, Pause, Play, ArrowDownToLine } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { useData } from '@/lib/use-data'
import { PageSpinner } from '@/pages/groups'

export function LogsPage() {
  const [paused, setPaused] = useState(false)
  const { data, loading } = useData(() => api.logs(800), paused ? undefined : 5000)
  const boxRef = useRef<HTMLPreElement>(null)
  const [follow, setFollow] = useState(true)

  useEffect(() => {
    if (follow && boxRef.current) {
      boxRef.current.scrollTop = boxRef.current.scrollHeight
    }
  }, [data, follow])

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <span className="flex items-center gap-1.5 text-[11px] text-muted">
          {!paused && <span className="size-1.5 animate-pulse-soft rounded-full bg-success" />}
          {paused ? 'التحديث متوقف' : 'يتحدث تلقائياً كل ٥ ثوانٍ'}
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setPaused((v) => !v)}>
            {paused ? <Play /> : <Pause />}
            {paused ? 'استئناف' : 'إيقاف مؤقت'}
          </Button>
          <Button
            variant={follow ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFollow((v) => !v)}
          >
            <ArrowDownToLine />
            تتبع النهاية
          </Button>
        </div>
      </div>

      {loading && !data ? (
        <PageSpinner />
      ) : (
        <Card className="overflow-hidden p-0">
          {!data?.content ? (
            <div className="grid place-items-center gap-3 p-10 text-center text-muted">
              <ScrollText className="size-8" />
              <p className="text-sm">لا توجد سجلات بعد</p>
            </div>
          ) : (
            <pre
              ref={boxRef}
              dir="ltr"
              onScroll={(e) => {
                const el = e.currentTarget
                const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
                if (!atBottom && follow) setFollow(false)
              }}
              className="max-h-[70dvh] overflow-auto bg-bg/70 p-4 font-mono text-[11.5px] leading-relaxed text-ink/85"
            >
              {data.content}
            </pre>
          )}
        </Card>
      )}
    </div>
  )
}
