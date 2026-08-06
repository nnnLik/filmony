import { useEffect, useRef, useState, type CSSProperties } from 'react'

import type { StreakBatchItem } from '../../api/streaksTypes'
import { formatDaysCount } from '../../lib/formatRuPlural'
import { streakFlameStyleVars, streakHeat } from '../../lib/streakHeat'

import './ratingStreakStyles.css'

export type RatingStreakBadgeProps = {
  item: StreakBatchItem
  className?: string
}

export function RatingStreakBadge({ item, className = '' }: RatingStreakBadgeProps) {
  const [pop, setPop] = useState(false)
  const [open, setOpen] = useState(false)
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
  const style = {
    '--streak-heat': String(heat),
    ...streakFlameStyleVars(heat),
  } as CSSProperties
  const daysLabel = formatDaysCount(current)

  return (
    <span
      className={`relative inline-flex ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="rating-streak-badge relative inline-flex items-center before:absolute before:-inset-x-1 before:-inset-y-2 before:content-['']"
        style={style}
        aria-label={`Серия оценок: ${daysLabel} подряд`}
        onClick={(e) => {
          e.stopPropagation()
          e.preventDefault()
          setOpen((v) => !v)
        }}
      >
        <span className={`rating-streak-badge__digit ${pop ? 'rating-streak-badge__digit--pop' : ''}`}>{current}</span>
      </button>
      {open ? (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-30 mt-1 min-w-[9rem] rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-left shadow-lg"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-xs text-(--tgui--hint_color)">Серия оценок</p>
          <p className="mt-0.5 text-sm text-(--tgui--text_color)">
            {daysLabel} подряд вы ставите оценки фильмам.
          </p>
        </span>
      ) : null}
    </span>
  )
}
