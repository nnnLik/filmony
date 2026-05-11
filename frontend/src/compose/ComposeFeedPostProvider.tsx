import { useCallback, useMemo, useState, type ReactNode } from 'react'

import { FeedComposeSheet } from '../components/feed/FeedComposeSheet'

import { ComposeFeedPostContext } from './composeFeedPostContext'
import type { OpenComposeFeedPostPayload } from './feedComposeTypes'

export function ComposeFeedPostProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [composeSessionKey, setComposeSessionKey] = useState(0)
  const [sourceCommentId, setSourceCommentId] = useState<number | null>(null)
  const [referencedMovieCardId, setReferencedMovieCardId] = useState<number | null>(null)

  const openCompose = useCallback((payload?: OpenComposeFeedPostPayload) => {
    setSourceCommentId(payload?.sourceCommentId ?? null)
    setReferencedMovieCardId(payload?.referencedMovieCardId ?? null)
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
        <FeedComposeSheet
          key={composeSessionKey}
          onClose={closeCompose}
          sourceCommentId={sourceCommentId}
          referencedMovieCardId={referencedMovieCardId}
        />
      ) : null}
    </ComposeFeedPostContext.Provider>
  )
}
