import { Title } from '@telegram-apps/telegram-ui'
import type { ReactNode } from 'react'

import { formatRating } from '../feed/feedCardUtils'

type CatalogEntitySummaryCardProps = {
  title: string
  filmsCount: number
  avgCommunityRating?: number | null
  posterUrl?: string | null
  className?: string
  footer?: ReactNode
}

export function CatalogEntitySummaryCard({
  title,
  filmsCount,
  avgCommunityRating,
  posterUrl,
  className,
  footer,
}: CatalogEntitySummaryCardProps) {
  return (
    <div className={className}>
      <div className={posterUrl != null ? 'flex items-center gap-4' : undefined}>
        {posterUrl != null ? (
          <img
            src={posterUrl}
            alt=""
            className="size-20 shrink-0 rounded-full object-cover bg-(--tgui--secondary_bg_color)"
            loading="lazy"
            decoding="async"
          />
        ) : null}
        <div className="min-w-0 flex-1">
          <Title level="2" weight="2">
            {title}
          </Title>
          <div className="mt-3 flex flex-wrap gap-3 text-sm tabular-nums text-(--tgui--hint_color)">
            <span>
              <span className="font-semibold text-(--tgui--text_color)">{filmsCount}</span> фильмов с
              оценками
            </span>
            {avgCommunityRating != null ? (
              <span>
                средняя{' '}
                <span className="font-semibold text-(--tgui--text_color)">
                  {formatRating(avgCommunityRating)}
                </span>
              </span>
            ) : null}
          </div>
          {footer}
        </div>
      </div>
    </div>
  )
}
