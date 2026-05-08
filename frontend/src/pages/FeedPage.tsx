import { Button } from '@telegram-apps/telegram-ui'
import { ChevronDown } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { getMovieCardFeedPage } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import type {
  FeedListMode,
  FeedMovieCard,
  MovieCardComment,
} from '../api/profileTypes'
import { FeedCard } from '../components/feed/FeedCard'
import { FeedCardSkeleton } from '../components/feed/FeedCardSkeleton'
import { FeedModePickerSheet, feedModeTitle } from '../components/feed/FeedModePickerSheet'

export function FeedPage() {
  const aliveRef = useRef(true)

  useEffect(() => {
    aliveRef.current = true
    return () => {
      aliveRef.current = false
    }
  }, [])

  const [items, setItems] = useState<FeedMovieCard[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [feedMode, setFeedMode] = useState<FeedListMode>('default')
  const [modeSheetOpen, setModeSheetOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadInitial = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const page = await getMovieCardFeedPage({ limit: 20, mode: feedMode })
      if (!aliveRef.current) return
      setItems(page.items)
      setNextCursor(page.next_cursor ?? null)
    } catch (e) {
      if (!aliveRef.current) return
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить ленту')
    } finally {
      if (aliveRef.current) {
        setLoading(false)
      }
    }
  }, [feedMode])

  useEffect(() => {
    queueMicrotask(() => {
      void loadInitial()
    })
  }, [loadInitial])

  const loadMore = useCallback(async () => {
    if (nextCursor == null || loadingMore) return
    setLoadingMore(true)
    try {
      const page = await getMovieCardFeedPage({ cursor: nextCursor, limit: 20, mode: feedMode })
      if (!aliveRef.current) return
      setItems((prev) => [...prev, ...page.items])
      setNextCursor(page.next_cursor ?? null)
    } catch (e) {
      if (!aliveRef.current) return
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить ещё карточки')
    } finally {
      if (aliveRef.current) {
        setLoadingMore(false)
      }
    }
  }, [nextCursor, loadingMore, feedMode])

  const onCommentsState = useCallback(
    (cardId: number, next: { comments_count: number; comments_preview: MovieCardComment[] }) => {
      setItems((prev) =>
        prev.map((c) => (c.id === cardId ? { ...c, ...next } : c))
      )
    },
    []
  )

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center gap-2 px-4 py-3">
          <h1 className="min-w-0 flex-1 truncate bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
            Лента
          </h1>
          <div className="flex shrink-0 items-center gap-1.5">
            <Button
              mode="gray"
              size="s"
              type="button"
              className="inline-flex max-w-42 min-w-0 shrink items-center gap-1"
              onClick={() => setModeSheetOpen(true)}
              aria-haspopup="dialog"
              aria-expanded={modeSheetOpen}
              aria-label={`Источник ленты: ${feedModeTitle(feedMode)}. Открыть выбор`}
            >
              <span className="min-w-0 truncate">{feedModeTitle(feedMode)}</span>
              <ChevronDown className="block size-4 shrink-0 opacity-75" aria-hidden />
            </Button>
            <Link to="/cards/new" aria-label="Добавить фильм" className="shrink-0 no-underline">
              <Button mode="gray">+</Button>
            </Link>
          </div>
        </div>
      </header>

      <FeedModePickerSheet
        open={modeSheetOpen}
        onClose={() => setModeSheetOpen(false)}
        value={feedMode}
        onSelect={setFeedMode}
      />

      <main className="max-w-full overflow-x-hidden px-4 pb-10 pt-3">
        <div className="flex flex-col gap-5">
          {loading && (
            <div className="flex flex-col gap-4">
              <FeedCardSkeleton />
              <FeedCardSkeleton />
              <FeedCardSkeleton />
            </div>
          )}

          {!loading && error != null && (
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-4">
              <p className="text-[14px] text-(--tgui--hint_color)">{error}</p>
              <Button stretched className="mt-4" onClick={() => void loadInitial()}>
                Повторить
              </Button>
            </div>
          )}

          {!loading && error == null && items.length === 0 && (
            <div className="flex flex-col items-center gap-4 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-10">
              <p className="text-center text-[14px] leading-relaxed text-(--tgui--hint_color)">
                Здесь появятся карточки пользователей. Добавьте свой фильм первым.
              </p>
              <Link to="/cards/new" className="w-full no-underline">
                <Button stretched>Добавить фильм</Button>
              </Link>
            </div>
          )}

          {!loading && error == null && items.length > 0 && (
            <>
              {items.map((card) => (
                <FeedCard key={card.id} card={card} onCommentsState={onCommentsState} />
              ))}
              {nextCursor != null ? (
                <div className="flex justify-center pt-1 pb-4">
                  <Button
                    mode="gray"
                    stretched
                    disabled={loadingMore}
                    onClick={() => void loadMore()}
                  >
                    {loadingMore ? 'Загрузка…' : 'Загрузить ещё'}
                  </Button>
                </div>
              ) : null}
            </>
          )}
        </div>
      </main>
    </div>
  )
}
