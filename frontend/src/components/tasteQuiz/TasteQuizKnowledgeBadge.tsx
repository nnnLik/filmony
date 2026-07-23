import { useState } from 'react'

import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import { tasteQuizAccuracyColor } from '../../lib/tasteQuizAccuracyColor'

export type TasteQuizKnowledgeBadgeProps = {
  item: TasteQuizKnowledgeBatchItem
  className?: string
}

export function TasteQuizKnowledgeBadge({ item, className = '' }: TasteQuizKnowledgeBadgeProps) {
  const [open, setOpen] = useState(false)

  if (item.attempts <= 0) {
    return null
  }

  const color = tasteQuizAccuracyColor(item.accuracy_pct)

  return (
    <span className={`relative inline-flex ${className}`}>
      <button
        type="button"
        className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg px-1 py-0.5 text-xs leading-none"
        aria-label={`Точность угадывания ${item.accuracy_pct} процентов, ${item.attempts} попыток`}
        onClick={(e) => {
          e.stopPropagation()
          e.preventDefault()
          setOpen((v) => !v)
        }}
      >
        <span className="text-(--tgui--hint_color)">(</span>
        <span className="font-medium tabular-nums" style={{ color }}>
          {item.accuracy_pct}%
        </span>
        <span className="text-(--tgui--hint_color)">)</span>
      </button>
      {open ? (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-30 mt-1 min-w-[9rem] rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-left shadow-lg"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-xs text-(--tgui--hint_color)">Угадывание вкуса</p>
          <p className="mt-0.5 text-sm tabular-nums text-(--tgui--text_color)">
            {item.points_sum} очк. · {item.attempts} попыток
          </p>
        </span>
      ) : null}
    </span>
  )
}
