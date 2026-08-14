import { Button } from '@telegram-apps/telegram-ui'
import type { RefObject } from 'react'
import { Link } from 'react-router'

import type { WatchlistEntryItem } from '../../api/profileTypes'
import { EveningForTwoSection } from '../watchlist/EveningForTwoSection'
import { WatchlistOverlapSection } from '../watchlist/WatchlistOverlapSection'
import { ProfileTabSkeleton } from './ProfileTabSkeleton'
import { WatchlistPosterGrid } from './WatchlistPosterGrid'

type ProfileWatchlistPanelProps = {
  watchlist: { items: WatchlistEntryItem[]; next_cursor: string | null } | null
  error: string | null
  loading?: boolean
  canLoadMore: boolean
  isFetchingNextPage: boolean
  loadMoreRef: RefObject<HTMLDivElement | null>
  showOverlapSection?: boolean
  showAddWhenEmpty?: boolean
  errorClassName?: string
  emptyClassName?: string
  gridClassName?: string
  loadMoreClassName?: string
}

export function ProfileWatchlistPanel({
  watchlist,
  error,
  loading = false,
  canLoadMore,
  isFetchingNextPage,
  loadMoreRef,
  showOverlapSection = false,
  showAddWhenEmpty = false,
  errorClassName = 'filmony-text-panel mb-2 text-center text-sm text-(--tgui--destructive_text_color)',
  emptyClassName,
  gridClassName = 'px-1',
  loadMoreClassName,
}: ProfileWatchlistPanelProps) {
  return (
    <>
      {showOverlapSection ? (
        <>
          <EveningForTwoSection enabled={!loading} />
          <WatchlistOverlapSection enabled={!loading} title="Оба хотите посмотреть" />
        </>
      ) : null}
      {error != null ? <p className={errorClassName}>{error}</p> : null}
      {loading ? <ProfileTabSkeleton /> : null}
      {!loading && watchlist != null && watchlist.items.length === 0 ? (
        showAddWhenEmpty ? (
          <div className={`filmony-text-panel flex flex-col items-center gap-4 py-8 text-center ${emptyClassName ?? ''}`}>
            <p className="text-sm text-(--tgui--hint_color)">В списке «Позже» пока пусто</p>
            <Link to="/cards/new" className="w-full max-w-xs no-underline">
              <Button stretched>Добавить в список</Button>
            </Link>
          </div>
        ) : (
          <p
            className={`filmony-text-panel text-center text-sm text-(--tgui--hint_color) ${emptyClassName ?? 'mx-4 my-4'}`}
          >
            В списке «Позже» пока пусто.
          </p>
        )
      ) : null}
      {!loading && watchlist != null && watchlist.items.length > 0 ? (
        <div className={gridClassName}>
          <WatchlistPosterGrid items={watchlist.items} />
        </div>
      ) : null}
      {canLoadMore ? (
        <div className={loadMoreClassName}>
          <div ref={loadMoreRef} className="mt-2 h-1 w-full shrink-0" aria-hidden />
          {isFetchingNextPage ? (
            <p className="mt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем список…</p>
          ) : null}
        </div>
      ) : null}
    </>
  )
}
