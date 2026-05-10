import { useEffect, useRef } from 'react'

type Options = {
  /** Подгружать следующую страницу, пока пользователь не ушёл со страницы / сегмента */
  enabled: boolean
  /** Уже идёт запрос — не дёргать повторно */
  isBusy: boolean
  onLoadMore: () => void | Promise<void>
  /** Зона срабатывания до появления элемента в видимой области (px) */
  rootMargin?: string
}

/**
 * Вызывает onLoadMore, когда невидимый sentinel попадает в зону прокрутки (или близко к ней).
 */
export function useInfiniteScrollLoadMore({
  enabled,
  isBusy,
  onLoadMore,
  rootMargin = '160px',
}: Options) {
  const sentinelRef = useRef<HTMLDivElement | null>(null)
  const onLoadMoreRef = useRef(onLoadMore)

  useEffect(() => {
    onLoadMoreRef.current = onLoadMore
  }, [onLoadMore])

  useEffect(() => {
    const el = sentinelRef.current
    if (el == null) {
      return
    }
    const obs = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) {
          return
        }
        if (!enabled || isBusy) {
          return
        }
        void onLoadMoreRef.current()
      },
      { root: null, rootMargin, threshold: 0 },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [enabled, isBusy, rootMargin])

  return sentinelRef
}
