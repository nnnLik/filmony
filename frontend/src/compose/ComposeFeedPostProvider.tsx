import { lazy, Suspense, useCallback, useMemo, useState, type ReactNode } from 'react'

import { ComposeFeedPostContext } from './composeFeedPostContext'
import type { OpenComposeFeedPostPayload } from './feedComposeTypes'

const FeedComposeSheet = lazy(async () => {
  const m = await import('../components/feed/FeedComposeSheet')
  return { default: m.FeedComposeSheet }
})

export function ComposeFeedPostProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [composeSessionKey, setComposeSessionKey] = useState(0)
  const [sourceCommentId, setSourceCommentId] = useState<number | null>(null)
  const [referencedMovieCardId, setReferencedMovieCardId] = useState<number | null>(null)
  const [sourceCommentImageUrl, setSourceCommentImageUrl] = useState<string | null>(null)

  const openCompose = useCallback((payload?: OpenComposeFeedPostPayload) => {
    setSourceCommentId(payload?.sourceCommentId ?? null)
    setReferencedMovieCardId(payload?.referencedMovieCardId ?? null)
    setSourceCommentImageUrl(
      payload?.sourceCommentImageUrl != null && payload.sourceCommentImageUrl.trim() !== ''
        ? payload.sourceCommentImageUrl.trim()
        : null,
    )
    setComposeSessionKey((k) => k + 1)
    setOpen(true)
  }, [])

  const closeCompose = useCallback(() => {
    setOpen(false)
  }, [])

  const value = useMemo(
    () => ({ openCompose, closeCompose }),
    [openCompose, closeCompose],
  )

  return (
    <ComposeFeedPostContext.Provider value={value}>
      {children}
      {open ? (
        <Suspense fallback={null}>
          <FeedComposeSheet
            key={composeSessionKey}
            onClose={closeCompose}
            sourceCommentId={sourceCommentId}
            referencedMovieCardId={referencedMovieCardId}
            sourceCommentImageUrl={sourceCommentImageUrl}
          />
        </Suspense>
      ) : null}
    </ComposeFeedPostContext.Provider>
  )
}
