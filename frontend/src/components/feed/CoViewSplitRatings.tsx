import { Link } from 'react-router'
import type { MouseEventHandler } from 'react'

import type { CoViewSplit } from '../../api/feedInFeedTypes'
import { formatRating, ratingDashOffset, ratingPalette } from './feedCardUtils'

export type CoViewSplitRatingsProps = {
  splits: readonly CoViewSplit[]
  className?: string
  onLinkClick?: MouseEventHandler<HTMLAnchorElement>
}

export function CoViewSplitRatings({ splits, className = '', onLinkClick }: CoViewSplitRatingsProps) {
  if (splits.length === 0) {
    return null
  }

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-(--tgui--hint_color)">
        Смотрели вместе
      </p>
      <div className="flex flex-wrap gap-2">
        {splits.map((split) => {
          const palette = ratingPalette(split.rating)
          const dashOffset = ratingDashOffset(split.rating)
          return (
            <Link
              key={split.user_id}
              to={`/u/${encodeURIComponent(split.user_id)}`}
              onClick={onLinkClick}
              className="flex min-w-0 items-center gap-1.5 rounded-lg border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] px-2 py-1 no-underline transition-opacity active:opacity-90"
            >
              <span className="truncate text-xs font-medium text-(--tgui--link_color)">@{split.slug}</span>
              <span
                className="relative flex size-7 shrink-0 items-center justify-center rounded-full"
                style={{
                  backgroundColor: palette.track,
                  boxShadow: `inset 0 0 10px ${palette.glow}`,
                }}
                aria-hidden
              >
                <svg viewBox="0 0 80 80" className="absolute size-7 -rotate-90">
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
                  />
                </svg>
                <span className="relative text-[10px] font-bold tabular-nums text-white drop-shadow-sm">
                  {formatRating(split.rating)}
                </span>
              </span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
