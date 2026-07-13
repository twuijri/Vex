import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold',
    'transition-[transform,box-shadow,background-color,border-color,color,filter] duration-200 ease-out',
    'will-change-transform select-none',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
    'disabled:cursor-not-allowed [&_svg]:size-4 [&_svg]:shrink-0 enabled:active:scale-[0.97]',
  ].join(' '),
  {
    variants: {
      variant: {
        primary: [
          'bg-gradient-accent text-accent-fg shadow-glow',
          'enabled:hover:shadow-glow-strong enabled:hover:-translate-y-0.5 enabled:hover:brightness-110',
          'disabled:bg-none disabled:bg-accent/15 disabled:text-ink/70 disabled:border disabled:border-accent/40 disabled:shadow-none',
        ].join(' '),
        secondary: [
          'bg-bg-elev text-ink border border-border',
          'enabled:hover:border-accent/40 enabled:hover:bg-bg-elev/80 enabled:hover:-translate-y-0.5',
          'disabled:opacity-60',
        ].join(' '),
        ghost: 'text-muted enabled:hover:text-ink enabled:hover:bg-bg-elev/60 disabled:opacity-50',
        outline: [
          'border border-border bg-transparent text-ink',
          'enabled:hover:border-accent/50 enabled:hover:bg-accent/5 enabled:hover:-translate-y-0.5',
          'disabled:opacity-50',
        ].join(' '),
        danger: 'bg-danger/15 text-danger border border-danger/40 enabled:hover:bg-danger/25',
      },
      size: {
        sm: 'h-9 px-3 text-xs',
        md: 'h-11 px-5',
        lg: 'h-12 px-6 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
)
Button.displayName = 'Button'
