import { useCallback, useMemo, useState, type ReactNode } from 'react'

import type { FeedPageItem } from '../api/feedListPageTypes'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useWatchingNowOfUsers } from '../hooks/useWatchingNowOfUsers'
import { collectFeedPrimaryAuthorIds } from '../lib/feedVisibleAuthorIds'

import {
  FeedAuthorBadgesContext,
  type FeedAuthorBadgesContextValue,
} from './feedAuthorBadgesContext'

const FEED_BADGE_STALE_TIME_MS = 5 * 60_000
const FEED_BADGE_GC_TIME_MS = 30 * 60_000

function dedupeUserIds(ids: Iterable<string>): string[] {
  return [...new Set([...ids].filter((id) => id.trim() !== ''))].sort()
}

function mergeUserIds(...groups: readonly string[][]): string[] {
  const merged = new Set<string>()
  for (const group of groups) {
    for (const id of group) {
      if (id.trim() !== '') {
        merged.add(id)
      }
    }
  }
  return [...merged].sort()
}

export type FeedAuthorBadgesProviderProps = {
  items: FeedPageItem[]
  viewerUserId: string | null
  children: ReactNode
}

export function FeedAuthorBadgesProvider({
  items,
  viewerUserId,
  children,
}: FeedAuthorBadgesProviderProps) {
  const [commentAuthorsByScope, setCommentAuthorsByScope] = useState<Map<string, string[]>>(
    () => new Map(),
  )

  const registerCommentAuthors = useCallback((scopeKey: string, ids: readonly string[]) => {
    const normalized = dedupeUserIds(ids)
    setCommentAuthorsByScope((previous) => {
      const existing = previous.get(scopeKey)
      const unchanged =
        existing != null &&
        existing.length === normalized.length &&
        existing.every((id, index) => id === normalized[index])
      if (unchanged) {
        return previous
      }
      const next = new Map(previous)
      if (normalized.length === 0) {
        next.delete(scopeKey)
      } else {
        next.set(scopeKey, normalized)
      }
      return next
    })
  }, [])

  const primaryAuthorIds = useMemo(
    () => collectFeedPrimaryAuthorIds(items, viewerUserId),
    [items, viewerUserId],
  )

  const registeredCommentAuthorIds = useMemo(() => {
    const merged = new Set<string>()
    for (const ids of commentAuthorsByScope.values()) {
      for (const id of ids) {
        if (id.trim() !== '') {
          merged.add(id)
        }
      }
    }
    return [...merged].sort()
  }, [commentAuthorsByScope])

  const tasteQuizOwnerIds = useMemo(
    () => mergeUserIds(primaryAuthorIds.tasteQuizOwnerIds, registeredCommentAuthorIds),
    [primaryAuthorIds.tasteQuizOwnerIds, registeredCommentAuthorIds],
  )

  const streakUserIds = useMemo(
    () => mergeUserIds(primaryAuthorIds.streakUserIds, registeredCommentAuthorIds),
    [primaryAuthorIds.streakUserIds, registeredCommentAuthorIds],
  )

  const watchingUserIds = streakUserIds

  const { knowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(tasteQuizOwnerIds, {
    enabled: tasteQuizOwnerIds.length > 0,
    staleTime: FEED_BADGE_STALE_TIME_MS,
    gcTime: FEED_BADGE_GC_TIME_MS,
  })

  const { streakByUserId } = useRatingStreaksOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
    staleTime: FEED_BADGE_STALE_TIME_MS,
    gcTime: FEED_BADGE_GC_TIME_MS,
  })

  const { watchingByUserId } = useWatchingNowOfUsers(watchingUserIds, {
    enabled: watchingUserIds.length > 0,
    staleTime: 60_000,
    gcTime: FEED_BADGE_GC_TIME_MS,
    refetchInterval: 60_000,
  })

  const value = useMemo<FeedAuthorBadgesContextValue>(
    () => ({
      knowledgeByOwnerId,
      streakByUserId,
      watchingByUserId,
      registerCommentAuthors,
    }),
    [knowledgeByOwnerId, streakByUserId, watchingByUserId, registerCommentAuthors],
  )

  return (
    <FeedAuthorBadgesContext.Provider value={value}>{children}</FeedAuthorBadgesContext.Provider>
  )
}
