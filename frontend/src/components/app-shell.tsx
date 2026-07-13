import { type ReactNode, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Users2, UserX, Bot, LineChart, PencilRuler,
  ScrollText, ChevronsLeft, ChevronsRight, LogOut, Menu, X,
} from 'lucide-react'
import { BrandMark } from '@/components/brand-mark'
import { useRoute, navigate } from '@/lib/router'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

type Item = { path: string; label: string; sub: string; icon: typeof LayoutDashboard }
type Group = { section: string; items: Item[] }

const GROUPS: Group[] = [
  {
    section: 'الرئيسية',
    items: [
      { path: '/', label: 'لوحة التحكم', sub: 'نظرة عامة', icon: LayoutDashboard },
    ],
  },
  {
    section: 'الإدارة',
    items: [
      { path: '/groups', label: 'المجموعات', sub: 'المجموعات المُدارة', icon: Users2 },
      { path: '/users', label: 'المستخدمون', sub: 'المحظورون', icon: UserX },
    ],
  },
  {
    section: 'الذكاء الاصطناعي',
    items: [
      { path: '/providers', label: 'المزودون', sub: 'الاتصالات والموديلات', icon: Bot },
      { path: '/stats', label: 'الإحصائيات', sub: 'الاستخدام والأخطاء', icon: LineChart },
      { path: '/prompt', label: 'البرومبت', sub: 'القواعد والعتبات', icon: PencilRuler },
    ],
  },
  {
    section: 'النظام',
    items: [
      { path: '/logs', label: 'السجلات', sub: 'سجل التطبيق', icon: ScrollText },
    ],
  },
]

export function AppShell({
  children, botUsername, onLogout,
}: { children: ReactNode; botUsername: string | null; onLogout: () => void }) {
  const path = useRoute()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    document.title = `${titleFor(path)} · Vex`
    setMobileOpen(false)
  }, [path])

  const nav = (
    <>
      <div className="flex h-16 items-center gap-2.5 px-4">
        <BrandMark size={30} />
        {!collapsed && (
          <span className="flex min-w-0 flex-col leading-tight">
            <span className="text-base font-bold tracking-tight wordmark">Vex</span>
            {botUsername && (
              <span className="truncate text-[10px] text-muted" dir="ltr">@{botUsername}</span>
            )}
          </span>
        )}
      </div>

      <nav className="flex-1 space-y-4 overflow-y-auto px-2.5 py-2">
        {GROUPS.map((g) => (
          <div key={g.section} className="space-y-1">
            {!collapsed && (
              <p className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-muted/70">{g.section}</p>
            )}
            {g.items.map((item) => {
              const active = item.path === path || (item.path !== '/' && path.startsWith(item.path))
              const Icon = item.icon
              return (
                <button
                  key={item.path}
                  type="button"
                  onClick={() => navigate(item.path)}
                  title={item.label}
                  className={cn(
                    'group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-start',
                    'transition-all duration-200 ease-out active:scale-[0.98]',
                    active ? 'text-ink' : 'text-muted hover:bg-bg-elev/70 hover:text-ink'
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="sidebar-active"
                      className="absolute inset-0 -z-10 rounded-xl bg-gradient-to-r from-accent/20 to-accent/5 ring-1 ring-accent/30"
                      transition={{ type: 'spring', bounce: 0.18, duration: 0.45 }}
                    />
                  )}
                  <Icon className={cn('size-[18px] shrink-0', active && 'text-accent-from')} strokeWidth={2.2} />
                  {!collapsed && (
                    <span className="flex min-w-0 flex-col leading-tight">
                      <span className="text-sm font-semibold">{item.label}</span>
                      <span className="truncate text-[11px] text-muted">{item.sub}</span>
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      <div className="hidden border-t border-border px-2.5 py-3 md:block">
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium text-muted transition-colors hover:bg-bg-elev/70 hover:text-ink"
        >
          {collapsed
            ? <ChevronsRight className="size-4 rtl-flip" />
            : (<><ChevronsLeft className="size-4 rtl-flip" /><span>طيّ القائمة</span></>)}
        </button>
      </div>
    </>
  )

  return (
    <div className="relative flex min-h-dvh w-full gap-0 bg-bg text-ink spotlight-bg">
      {/* Desktop floating glass sidebar */}
      <aside
        className={cn(
          'sticky top-3 z-30 m-3 me-0 hidden h-[calc(100dvh-1.5rem)] shrink-0 flex-col rounded-3xl border border-border/70 glass-card shadow-card transition-all md:flex',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {nav}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0 bg-bg/70 backdrop-blur-sm" />
          <aside
            className="absolute inset-y-3 end-3 flex w-64 flex-col rounded-3xl border border-border/70 glass-card shadow-card"
            onClick={(e) => e.stopPropagation()}
          >
            {nav}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-border bg-bg/85 px-5 backdrop-blur-md sm:px-7">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileOpen((v) => !v)}
              className="grid size-9 place-items-center rounded-xl text-muted hover:bg-bg-elev/70 hover:text-ink md:hidden"
            >
              {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
            <h1 className="text-base font-semibold tracking-tight">{titleFor(path)}</h1>
          </div>
          <button
            type="button"
            onClick={async () => { try { await api.logout() } finally { onLogout() } }}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-bg-elev/50 px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-danger/40 hover:text-danger"
          >
            <LogOut className="size-3.5 rtl-flip" />
            <span className="hidden sm:inline">خروج</span>
          </button>
        </header>

        <main className="relative flex-1 px-5 py-6 sm:px-7 sm:py-8">{children}</main>
      </div>
    </div>
  )
}

function titleFor(path: string): string {
  for (const g of GROUPS) for (const it of g.items) {
    if (it.path === path || (it.path !== '/' && path.startsWith(it.path))) return it.label
  }
  return 'لوحة التحكم'
}
