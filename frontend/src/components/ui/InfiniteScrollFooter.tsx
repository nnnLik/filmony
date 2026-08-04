import type { RefObject } from 'react'

type InfiniteScrollFooterProps = {
  sentinelRef?: RefObject<HTMLDivElement | null>
  loading?: boolean
  loadingMessage?: string
  className?: string
}

export function InfiniteScrollFooter({
  sentinelRef,
  loading = false,
  loadingMessage = 'Подгружаем…',
  className,
}: InfiniteScrollFooterProps) {
  return (
    <div className={className}>
      {loading ? (
        <p className="py-3 text-center text-sm text-(--tgui--hint_color)">{loadingMessage}</p>
      ) : null}
      <div ref={sentinelRef} className="h-px w-full" aria-hidden />
    </div>
  )
}
