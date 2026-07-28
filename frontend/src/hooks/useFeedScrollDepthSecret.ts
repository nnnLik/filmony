import { useCallback, useEffect, useRef, useState } from 'react'

import {
  feedScrollSecretStorageKey,
  isScrollAtBottom,
  onFeedScrollBottomEdge,
  parseFeedScrollSecretSession,
  resolveMicroFunLine,
  serializeFeedScrollSecretSession,
} from '../lib/microFun'
import { safeHapticSuccess } from '../lib/safeHaptic'

type Options = {
  containerRef: React.RefObject<HTMLElement | null>
  userId: string | number | null
  enabled: boolean
  itemCount: number
  hasNextPage: boolean
  isFetchingNextPage: boolean
}

export function useFeedScrollDepthSecret({
  containerRef,
  userId,
  enabled,
  itemCount,
  hasNextPage,
  isFetchingNextPage,
}: Options) {
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const wasAtBottomRef = useRef(false)
  const sessionRef = useRef(parseFeedScrollSecretSession(null))
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    if (userId == null || typeof window === 'undefined') {
      sessionRef.current = { bottomHits: 0, triggered: false }
      return
    }
    sessionRef.current = parseFeedScrollSecretSession(
      window.sessionStorage.getItem(feedScrollSecretStorageKey(userId)),
    )
  }, [userId])

  const dismissToast = useCallback(() => {
    setToastMessage(null)
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (container == null || !enabled || userId == null || itemCount === 0) {
      return undefined
    }

    const canCountBottom = () => !hasNextPage && !isFetchingNextPage

    const handleScroll = () => {
      if (rafRef.current != null) {
        return
      }
      rafRef.current = window.requestAnimationFrame(() => {
        rafRef.current = null
        if (!canCountBottom()) {
          wasAtBottomRef.current = false
          return
        }

        const atBottom = isScrollAtBottom(
          container.scrollTop,
          container.clientHeight,
          container.scrollHeight,
        )
        const edge = onFeedScrollBottomEdge({
          wasAtBottom: wasAtBottomRef.current,
          isAtBottom: atBottom,
          session: sessionRef.current,
        })
        wasAtBottomRef.current = atBottom
        sessionRef.current = edge.nextState

        try {
          window.sessionStorage.setItem(
            feedScrollSecretStorageKey(userId),
            serializeFeedScrollSecretSession(edge.nextState),
          )
        } catch {
          /* quota / privacy mode */
        }

        if (edge.shouldTrigger) {
          const message = resolveMicroFunLine({
            poolKey: 'feed_scroll_depth_secret',
            fallback: 'Ты реально всё прочитал? Уважение.',
            userId,
          })
          setToastMessage(message)
          safeHapticSuccess()
        }
      })
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
      if (rafRef.current != null) {
        window.cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [
    containerRef,
    enabled,
    userId,
    itemCount,
    hasNextPage,
    isFetchingNextPage,
  ])

  return { toastMessage, dismissToast }
}
