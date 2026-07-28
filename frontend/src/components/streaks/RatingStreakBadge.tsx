import { useEffect, useRef, useState, type CSSProperties } from 'react'

import type { StreakBatchItem } from '../../api/streaksTypes'
import { streakHeat } from '../../lib/streakHeat'

import './ratingStreakStyles.css'

export type RatingStreakBadgeProps = {
  item: StreakBatchItem
  className?: string
}

export function RatingStreakBadge({ item, className = '' }: RatingStreakBadgeProps) {
  const [pop, setPop] = useState(false)
  const prevCurrentRef = useRef<number | null>(null)
  const current = item.current

  useEffect(() => {
    if (current <= 3) return
    const prev = prevCurrentRef.current
    if (prev != null && prev !== current) {
      setPop(true)
      const timer = window.setTimeout(() => setPop(false), 560)
      prevCurrentRef.current = current
      return () => window.clearTimeout(timer)
    }
    prevCurrentRef.current = current
    return undefined
  }, [current])

  if (current <= 3) {
    return null
  }

  const heat = streakHeat(current)
  const style = { '--streak-heat': String(heat) } as CSSProperties

  return (
    <span className={`rating-streak-badge ${className}`} style={style} aria-label={`Серия оценок ${current} дней`}>
      <span className="rating-streak-badge__fire" aria-hidden>
        🔥
      </span>
      <span className={`rating-streak-badge__number ${pop ? 'rating-streak-badge__number--pop' : ''}`}>
        {current}
      </span>
    </span>
  )
}
