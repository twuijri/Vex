import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'hsl(var(--bg) / <alpha-value>)',
        'bg-elev': 'hsl(var(--bg-elev) / <alpha-value>)',
        ink: 'hsl(var(--ink) / <alpha-value>)',
        muted: 'hsl(var(--muted) / <alpha-value>)',
        border: 'hsl(var(--border) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        accent: {
          DEFAULT: 'hsl(var(--accent) / <alpha-value>)',
          fg: 'hsl(var(--accent-fg) / <alpha-value>)',
          from: 'hsl(var(--accent-from) / <alpha-value>)',
          to: 'hsl(var(--accent-to) / <alpha-value>)',
        },
        success: 'hsl(var(--success) / <alpha-value>)',
        warning: 'hsl(var(--warning) / <alpha-value>)',
        danger: 'hsl(var(--danger) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans Arabic"', '"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: { '4xl': '2rem' },
      boxShadow: {
        glow: '0 0 80px -20px hsl(var(--accent) / 0.45)',
        'glow-strong': '0 0 120px -10px hsl(var(--accent) / 0.6)',
        card: '0 20px 60px -20px hsl(230 50% 3% / 0.5), 0 8px 24px -8px hsl(230 40% 5% / 0.4)',
      },
      backgroundImage: {
        'gradient-accent':
          'linear-gradient(135deg, hsl(var(--accent-from)) 0%, hsl(var(--accent-to)) 100%)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '0.7' },
          '50%': { opacity: '1' },
        },
        'border-spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out',
        'pulse-soft': 'pulse-soft 2.4s ease-in-out infinite',
        'border-spin': 'border-spin 6s linear infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
