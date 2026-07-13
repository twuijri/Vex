import * as React from 'react'
import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from '@/lib/utils'

export const inputCls =
  'w-full rounded-xl border border-border bg-bg/60 px-4 py-2.5 text-sm text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-accent/60 focus:ring-2 focus:ring-ring/30'

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="mb-1.5 block text-sm font-medium text-muted">{children}</label>
}

export function TextField({
  label, hint, className, ...props
}: { label?: string; hint?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="mb-4">
      {label && <Label>{label}</Label>}
      <input className={cn(inputCls, className)} {...props} />
      {hint && <p className="mt-1 text-xs text-muted/70">{hint}</p>}
    </div>
  )
}

export function SecretField({
  label, hint, ...props
}: { label?: string; hint?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  const [show, setShow] = useState(false)
  return (
    <div className="mb-4">
      {label && <Label>{label}</Label>}
      <div className="relative">
        <input className={cn(inputCls, 'pe-11 font-mono')} type={show ? 'text' : 'password'} dir="ltr" {...props} />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          className="absolute inset-y-0 end-2 my-auto grid size-7 place-items-center rounded-lg text-muted hover:text-ink"
        >
          {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>
      </div>
      {hint && <p className="mt-1 text-xs text-muted/70">{hint}</p>}
    </div>
  )
}

export function Select({
  label, children, className, ...props
}: { label?: string } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="mb-4">
      {label && <Label>{label}</Label>}
      <select className={cn(inputCls, 'appearance-none', className)} {...props}>
        {children}
      </select>
    </div>
  )
}

export function TextArea({
  label, hint, className, ...props
}: { label?: string; hint?: string } & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div className="mb-4">
      {label && <Label>{label}</Label>}
      <textarea className={cn(inputCls, 'min-h-32 leading-relaxed', className)} {...props} />
      {hint && <p className="mt-1 text-xs text-muted/70">{hint}</p>}
    </div>
  )
}

export function Toggle({
  checked, onChange, label, hint,
}: { checked: boolean; onChange: (v: boolean) => void; label?: string; hint?: string }) {
  return (
    <label className="flex cursor-pointer items-start gap-3">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full p-0.5 transition-colors',
          checked ? 'bg-accent' : 'bg-border'
        )}
      >
        <span className={cn('size-5 rounded-full bg-white transition-transform', checked ? '-translate-x-5 rtl:translate-x-0' : 'rtl:-translate-x-5')} />
      </button>
      {(label || hint) && (
        <span className="flex flex-col">
          {label && <span className="text-sm font-medium text-ink">{label}</span>}
          {hint && <span className="text-xs text-muted/70">{hint}</span>}
        </span>
      )}
    </label>
  )
}
