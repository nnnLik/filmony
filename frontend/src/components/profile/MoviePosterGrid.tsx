import { useState } from 'react'

import type { MovieCard } from '../../api/profileTypes'
import { movieCardPrimaryPoster, movieCardPrimaryTitle } from '../../lib/movieCardDisplay'
import { FilmGenreChips } from '../films/FilmGenreChips'
import { FeedRatingRing } from '../feed/FeedRatingRing'
import { FavoriteCardHeartButton } from '../cards/FavoriteCardHeartButton'
import { ContrarianBadge } from '../gamification/ContrarianBadge'
import { PosterGrid } from '../cards/PosterGrid'
import { PosterTile } from '../cards/PosterTile'

type MoviePosterGridProps = {
  items: MovieCard[]
  /** Показывать сердце и переключать избранное (только на своём профиле) */
  showFavoriteToggle?: boolean
  /** Показывать бейдж «контр-культ» (только на своём профиле) */
  showContrarianBadge?: boolean
  onFavoriteToggled?: (cardId: number, nextFavorite: boolean) => void
}

export function MoviePosterGrid({
  items,
  showFavoriteToggle = false,
  showContrarianBadge = false,
  onFavoriteToggled,
}: MoviePosterGridProps) {
  return (
    <PosterGrid>
      {items.map((card) => (
        <PosterCell
          key={card.id}
          card={card}
          showFavoriteToggle={showFavoriteToggle}
          showContrarianBadge={showContrarianBadge}
          onFavoriteToggled={onFavoriteToggled}
        />
      ))}
    </PosterGrid>
  )
}

function PosterCell({
  card,
  showFavoriteToggle,
  showContrarianBadge,
  onFavoriteToggled,
}: {
  card: MovieCard
  showFavoriteToggle: boolean
  showContrarianBadge: boolean
  onFavoriteToggled?: (cardId: number, nextFavorite: boolean) => void
}) {
  const primaryTitle = movieCardPrimaryTitle(card)
  const primaryPoster = movieCardPrimaryPoster(card)
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
    <PosterTile
      posterUrl={primaryPoster}
      title={primaryTitle}
      href={`/cards/${card.id}`}
      ariaLabel={`Открыть карточку «${primaryTitle}»`}
      footer={<FilmGenreChips genres={card.film_genres} maxVisible={2} className="px-1 py-1" />}
      overlay={
        <>
          {showContrarianBadge ? (
            <div className="absolute left-1 top-1 z-[3]">
              <ContrarianBadge
                rating={card.rating}
                communityAvgRating={card.community_avg_rating}
                isContrarian={card.is_contrarian}
              />
            </div>
          ) : null}
          <FeedRatingRing
            rating={card.rating}
            positionClassName={
              showFavoriteToggle
                ? 'absolute right-1 bottom-1 z-[2] sm:right-1.5 sm:bottom-1.5'
                : 'absolute right-1 top-1 z-[2] sm:right-1.5 sm:top-1.5'
            }
          />
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
        </>
      }
    />
  )
}
