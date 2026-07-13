export function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <rect width="24" height="24" rx="6" fill="hsl(228 34% 14%)" />
      <path
        d="M5 5l7 14 7-14"
        stroke="url(#vex-g)"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <defs>
        <linearGradient id="vex-g" x1="5" y1="5" x2="19" y2="19">
          <stop stopColor="hsl(43 96% 58%)" />
          <stop offset="1" stopColor="hsl(30 92% 60%)" />
        </linearGradient>
      </defs>
    </svg>
  )
}
