import type { RefObject } from 'react'

import type { ShelfPhysicsMode } from '../../api/gamificationTypes'
import type { MovieCard } from '../../api/profileTypes'
import { isDefaultRatedCardsQuery, type RatedCardsListQuery } from '../../lib/ratedCardsListQuery'
import { FavoriteMoviesStrip } from './FavoriteMoviesStrip'
import { ProfileShelfPhysics } from './gamification/ProfileShelfPhysics'
import { MoviePosterGrid } from './MoviePosterGrid'
import { ProfileRatedCardsFilters } from './ProfileRatedCardsFilters'
import { ProfileTabSkeleton } from './ProfileTabSkeleton'
import { TabEmptyState } from '../ui/TabEmptyState'

type ProfileRatedPanelProps = {
  profileUserId: string
  viewerUserId: string | null
  ratedQuery: RatedCardsListQuery
  onRatedQueryChange: (next: RatedCardsListQuery) => void
  enableCategoryFilter?: boolean
  favoriteStripItems: MovieCard[]
  cards: { items: MovieCard[]; next_cursor: string | null } | null
  loading: boolean
  error: string | null
  canLoadMore: boolean
  isFetchingNextPage: boolean
  loadMoreRef: RefObject<HTMLDivElement | null>
  emptyUserId?: string | null
  emptyFallback?: string
  filteredEmptyFallback?: string
  showFavoriteToggle?: boolean
  showContrarianBadge?: boolean
  onFavoriteToggled?: (cardId: number, nextFavorite: boolean) => void
  filtersClassName?: string
  gridClassName?: string
  errorClassName?: string
  refreshingClassName?: string
  emptyClassName?: string
  loadMoreClassName?: string
  shelfPhysicsMode?: ShelfPhysicsMode
}

export function ProfileRatedPanel({
  profileUserId,
  viewerUserId,
  ratedQuery,
  onRatedQueryChange,
  enableCategoryFilter,
  favoriteStripItems,
  cards,
  loading,
  error,
  canLoadMore,
  isFetchingNextPage,
  loadMoreRef,
  emptyUserId,
  emptyFallback = 'Ещё нет оценённых карточек',
  filteredEmptyFallback = 'Нет карточек с такими фильтрами',
  showFavoriteToggle = false,
  showContrarianBadge = false,
  onFavoriteToggled,
  filtersClassName,
  gridClassName = 'px-1',
  errorClassName = 'filmony-text-panel mb-2 text-center text-sm text-(--tgui--destructive_text_color)',
  refreshingClassName = 'filmony-text-panel mb-2 text-center text-xs text-(--tgui--hint_color)',
  emptyClassName,
  loadMoreClassName,
  shelfPhysicsMode,
}: ProfileRatedPanelProps) {
  const grid = (
    <MoviePosterGrid
      items={cards?.items ?? []}
      showFavoriteToggle={showFavoriteToggle}
      showContrarianBadge={showContrarianBadge}
      onFavoriteToggled={onFavoriteToggled}
    />
  )

  return (
    <>
      <FavoriteMoviesStrip items={favoriteStripItems} />
      <div className={filtersClassName}>
        <ProfileRatedCardsFilters
          profileUserId={profileUserId}
          viewerUserId={viewerUserId}
          cardsQuery={ratedQuery}
          onChange={onRatedQueryChange}
          enableCategoryFilter={enableCategoryFilter}
        />
      </div>
      {cards == null && loading ? <ProfileTabSkeleton /> : null}
      {loading && cards != null ? (
        <p className={refreshingClassName}>Обновляем список…</p>
      ) : null}
      {error != null ? <p className={errorClassName}>{error}</p> : null}
      {cards != null && cards.items.length === 0 && !loading ? (
        isDefaultRatedCardsQuery(ratedQuery) ? (
          <TabEmptyState
            poolKey="profile_cards_empty"
            fallback={emptyFallback}
            userId={emptyUserId ?? viewerUserId}
            className={emptyClassName}
          />
        ) : (
          <TabEmptyState
            fallback={filteredEmptyFallback}
            userId={emptyUserId ?? viewerUserId}
            className={emptyClassName}
          />
        )
      ) : null}
      {cards != null && cards.items.length > 0 ? (
        <div className={gridClassName}>
          {shelfPhysicsMode != null ? (
            <ProfileShelfPhysics mode={shelfPhysicsMode}>
              {grid}
            </ProfileShelfPhysics>
          ) : (
            grid
          )}
        </div>
      ) : null}
      {canLoadMore ? (
        <div className={loadMoreClassName}>
          <div ref={loadMoreRef} className="mt-2 h-1 w-full shrink-0" aria-hidden />
          {isFetchingNextPage ? (
            <p className="mt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем карточки…</p>
          ) : null}
        </div>
      ) : null}
    </>
  )
}
