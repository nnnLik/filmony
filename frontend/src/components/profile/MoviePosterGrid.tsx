import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { MovieCard } from '../../api/profileTypes'
import { FeedRatingRing } from '../feed/FeedRatingRing'
import { FavoriteCardHeartButton } from '../cards/FavoriteCardHeartButton'

type MoviePosterGridProps = {
  items: MovieCard[]
  /** Показывать сердце и переключать избранное (только на своём профиле) */
  showFavoriteToggle?: boolean
  onFavoriteToggled?: (cardId: number, nextFavorite: boolean) => void
}

export function MoviePosterGrid({ items, showFavoriteToggle = false, onFavoriteToggled }: MoviePosterGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {items.map((card) => (
        <PosterCell
          key={card.id}
          card={card}
          showFavoriteToggle={showFavoriteToggle}
          onFavoriteToggled={onFavoriteToggled}
        />
      ))}
    </div>
  )
}

function PosterCell({
  card,
  showFavoriteToggle,
  onFavoriteToggled,
}: {
  card: MovieCard
  showFavoriteToggle: boolean
  onFavoriteToggled?: (cardId: number, nextFavorite: boolean) => void
}) {
  const [favoriteSync, setFavoriteSync] = useState(() => ({
    cardId: card.id,
    isFavorite: card.is_favorite ?? false,
  }))
  const [fav, setFav] = useState(() => card.is_favorite ?? false)
  if (favoriteSync.cardId !== card.id || favoriteSync.isFavorite !== (card.is_favorite ?? false)) {
    const nextFavorite = card.is_favorite ?? false
    setFavoriteSync({ cardId: card.id, isFavorite: nextFavorite })
    setFav(nextFavorite)
  }

  return (
    <Link
      to={`/cards/${card.id}`}
      className="relative block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline"
      aria-label={`Открыть карточку «${card.film_title}»`}
    >
      <div className="relative aspect-2/3 w-full">
        {card.film_poster_url ? (
          <img src={card.film_poster_url} alt={card.film_title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
            Нет постера
          </div>
        )}
        <FeedRatingRing
          rating={card.rating}
          positionClassName={
            showFavoriteToggle
              ? 'absolute right-1 bottom-1 z-[2] sm:right-1.5 sm:bottom-1.5'
              : 'absolute right-1 top-1 z-[2] sm:right-1.5 sm:top-1.5'
          }
        />
      </div>
      {showFavoriteToggle ? (
        <div
          className="absolute right-1 top-1 z-[1]"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
          }}
          onKeyDown={(e) => e.stopPropagation()}
          role="presentation"
        >
          <FavoriteCardHeartButton
            cardId={card.id}
            isFavorite={fav}
            onFavoriteChange={(next) => {
              setFav(next)
              onFavoriteToggled?.(card.id, next)
            }}
          />
        </div>
      ) : null}
    </Link>
  )
}
