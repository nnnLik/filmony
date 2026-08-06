import { Trophy } from 'lucide-react'

import type { FilmAwardBadge } from '../../api/profileTypes'

type FilmAwardBadgeStripProps = {
  badges: FilmAwardBadge[]
  compact?: boolean
  className?: string
}

function badgeLabel(badge: FilmAwardBadge): string {
  const role =
    badge.kind === 'oscar_best_picture_winner'
      ? 'Оскар — лучший фильм (победитель)'
      : 'Оскар — лучший фильм (номинант)'
  return `${role}, ${badge.ceremony_year}`
}

export function FilmAwardBadgeStrip({
  badges,
  compact = false,
  className = '',
}: FilmAwardBadgeStripProps) {
  if (badges.length === 0) return null

  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      {badges.map((badge) => {
        const isWinner = badge.kind === 'oscar_best_picture_winner'
        const label = badgeLabel(badge)
        return (
          <span
            key={`${badge.kind}-${badge.ceremony_year}`}
            className={`inline-flex items-center gap-0.5 rounded-md border px-1.5 py-0.5 tabular-nums ${
              isWinner
                ? 'border-[color-mix(in_srgb,#eab308_45%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,#eab308_16%,var(--tgui--secondary_bg_color))] text-[#facc15]'
                : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) text-(--tgui--hint_color)'
            } ${compact ? 'text-[10px]' : 'text-[11px]'}`}
            title={label}
            aria-label={label}
          >
            <Trophy
              className={`block shrink-0 ${compact ? 'size-3' : 'size-3.5'} ${
                isWinner ? 'text-[#facc15]' : 'text-(--tgui--hint_color)'
              }`}
              aria-hidden
            />
            <span className="font-semibold">{badge.ceremony_year}</span>
          </span>
        )
      })}
    </div>
  )
}
