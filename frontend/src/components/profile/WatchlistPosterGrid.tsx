import { Link } from 'react-router-dom'

import type { WatchlistFilmItem } from '../../api/profileTypes'

type WatchlistPosterGridProps = {
  items: WatchlistFilmItem[]
}

export function WatchlistPosterGrid({ items }: WatchlistPosterGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {items.map((item) => (
        <Link
          key={item.film_id}
          to={`/films/${encodeURIComponent(String(item.film_id))}`}
          className="block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline"
          aria-label={`Открыть в каталоге «${item.film_title}»`}
        >
          <div className="aspect-2/3 w-full">
            {item.film_poster_url ? (
              <img
                src={item.film_poster_url}
                alt={item.film_title}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
                Нет постера
              </div>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}
