import { Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { getMovieCardFeedPage } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import type { FeedMovieCard, MovieCardComment } from '../api/profileTypes'
import { FeedCard } from '../components/feed/FeedCard'
import { FeedCardSkeleton } from '../components/feed/FeedCardSkeleton'

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
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadInitial = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const page = await getMovieCardFeedPage({ limit: 20 })
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
  }, [])

  useEffect(() => {
    queueMicrotask(() => {
      void loadInitial()
    })
  }, [loadInitial])

  const loadMore = useCallback(async () => {
    if (nextCursor == null || loadingMore) return
    setLoadingMore(true)
    try {
      const page = await getMovieCardFeedPage({ cursor: nextCursor, limit: 20 })
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
  }, [nextCursor, loadingMore])

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
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
              Filmony
            </h1>
          </div>
          <Link to="/cards/new" aria-label="Добавить фильм" className="no-underline">
            <Button mode="gray">+</Button>
          </Link>
        </div>
      </header>

      <main className="max-w-full overflow-x-hidden px-4 pb-10 pt-3">
        <div className="mb-8">
          <div className="flex items-center gap-2.5">
            <span
              className="h-9 w-[3px] shrink-0 rounded-full bg-linear-to-b from-(--filmony-mint,#5eead4) via-(--filmony-amber,#e8b86d) to-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] shadow-[0_0_14px_-1px_var(--filmony-mint,#5eead4)]"
              aria-hidden
            />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-medium uppercase tracking-wide text-(--filmony-mint,#5eead4)">
                Обзор
              </p>
              <h2 className="mt-1 text-[22px] font-semibold leading-tight tracking-[-0.02em] text-(--tgui--text_color)">
                Лента
              </h2>
              <p className="mt-2 max-w-[20rem] text-[13px] leading-snug text-(--tgui--hint_color)">
                Свежие оценки и обсуждения в одном списке
              </p>
            </div>
          </div>
          <div
            className="mt-6 h-px w-full rounded-full bg-[linear-gradient(90deg,transparent,color-mix(in_srgb,var(--filmony-mint,#5eead4)_28%,transparent),color-mix(in_srgb,var(--tgui--divider_color)_95%,transparent),transparent)]"
            aria-hidden
          />
        </div>

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
