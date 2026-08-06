import { Section } from '@telegram-apps/telegram-ui'
import { useEffect, useRef } from 'react'

import type { CollectionFilmItem } from '../../api/collectionsTypes'
import { InlineLoadingState } from '../ui/InlineLoadingState'
import { ListErrorState } from '../ui/ListErrorState'

import { CollectionFilmRow } from './CollectionFilmRow'

type CollectionFilmsListProps = {
  films: CollectionFilmItem[]
  isPending: boolean
  errorMessage: string | null
  onRetry: () => void
  hasNextPage: boolean
  isFetchingNextPage: boolean
  onLoadMore: () => void
}

export function CollectionFilmsList({
  films,
  isPending,
  errorMessage,
  onRetry,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
}: CollectionFilmsListProps) {
  const loadMoreRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = loadMoreRef.current
    if (node == null || !hasNextPage || isFetchingNextPage) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          onLoadMore()
        }
      },
      { rootMargin: '240px 0px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, onLoadMore])

  if (errorMessage != null) {
    return <ListErrorState message={errorMessage} onRetry={onRetry} />
  }

  if (isPending) {
    return <InlineLoadingState message="Загрузка фильмов…" />
  }

  if (films.length === 0) {
    return (
      <p className="filmony-text-panel py-6 text-center text-sm text-(--tgui--hint_color)">
        В коллекции пока нет фильмов.
      </p>
    )
  }

  return (
    <Section header="Фильмы">
      <ul className="divide-y divide-(--tgui--divider_color)">
        {films.map((film) => (
          <CollectionFilmRow key={film.film_id} film={film} />
        ))}
      </ul>
      {hasNextPage || isFetchingNextPage ? (
        <div ref={loadMoreRef} className="px-3 py-3">
          {isFetchingNextPage ? <InlineLoadingState message="Загрузка…" /> : null}
        </div>
      ) : null}
    </Section>
  )
}
