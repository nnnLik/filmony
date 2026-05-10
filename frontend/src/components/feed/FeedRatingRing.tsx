import { useMemo } from 'react'

import { formatRating, ratingDashOffset, ratingPalette } from './feedCardUtils'

export type FeedRatingRingProps = {
  rating: number
  /** Позиционирование относительно ближайшего `relative` предка, например `absolute right-2.5 top-2.5 z-[3]` */
  positionClassName: string
  /** Уменьшенный вариант для узких постеров (например горизонтальная полоска «Любимое») */
  compact?: boolean
}

export function FeedRatingRing({ rating, positionClassName, compact = false }: FeedRatingRingProps) {
  const palette = useMemo(() => ratingPalette(rating), [rating])
  const dashOffset = ratingDashOffset(rating)
  const frame = compact ? 'size-9' : 'size-12'
  const labelClass = compact ? 'text-[12px]' : 'text-[15px]'

  return (
    <div
      className={`pointer-events-none flex ${frame} shrink-0 select-none items-center justify-center rounded-full backdrop-blur-md ${positionClassName}`}
      style={{
        backgroundColor: palette.track,
        boxShadow: `0 6px 20px rgba(0,0,0,0.35), inset 0 0 20px ${palette.glow}`,
      }}
      aria-hidden
    >
      <svg viewBox="0 0 80 80" className={`absolute ${frame} -rotate-90`}>
        <circle cx="40" cy="40" fill="none" r="34" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <circle
          cx="40"
          cy="40"
          fill="none"
          r="34"
          stroke={palette.ring}
          strokeDasharray={219.99}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          strokeWidth="6"
          style={{ filter: `drop-shadow(0 0 6px ${palette.glow})` }}
        />
      </svg>
      <span className={`relative font-extrabold tabular-nums text-white drop-shadow-sm ${labelClass}`}>
        {formatRating(rating)}
      </span>
    </div>
  )
}
