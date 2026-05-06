import { Link } from 'react-router-dom'

import type { MovieCard } from '../../api/profileTypes'

type MoviePosterGridProps = {
  items: MovieCard[]
}

export function MoviePosterGrid({ items }: MoviePosterGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {items.map((card) => (
        <Link
          key={card.id}
          to={`/cards/${card.id}`}
          className="block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline"
          aria-label={`Открыть карточку фильма ${card.film_title}`}
        >
          <div className="aspect-2/3 w-full">
            {card.film_poster_url ? (
              <img src={card.film_poster_url} alt={card.film_title} className="h-full w-full object-cover" />
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
