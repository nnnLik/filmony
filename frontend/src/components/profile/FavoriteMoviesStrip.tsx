import { Link } from 'react-router-dom'

import type { MovieCard } from '../../api/profileTypes'
import { FeedRatingRing } from '../feed/FeedRatingRing'

export type FavoriteMoviesStripProps = {
  items: MovieCard[]
}

export function FavoriteMoviesStrip({ items }: FavoriteMoviesStripProps) {
  if (items.length === 0) {
    return null
  }
  return (
    <div className="mb-5">
      <p className="mb-2 px-1 text-sm font-semibold text-(--tgui--text_color)">Любимое</p>
      <div className="flex gap-2.5 overflow-x-auto overflow-y-hidden pb-1 pl-1 pr-1 pt-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {items.map((card) => (
          <Link
            key={card.id}
            to={`/cards/${card.id}`}
            className="w-[5.25rem] shrink-0 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_20%,transparent)]"
            aria-label={`Открыть карточку «${card.film_title}»`}
          >
            <div className="relative aspect-2/3 w-full">
              {card.film_poster_url ? (
                <img src={card.film_poster_url} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full min-h-[5.5rem] items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                  Нет постера
                </div>
              )}
              <FeedRatingRing
                rating={card.rating}
                compact
                positionClassName="absolute right-0.5 top-0.5 z-[2] sm:right-1 sm:top-1"
              />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
