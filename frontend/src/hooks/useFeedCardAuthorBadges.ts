import { useEffect, useMemo } from 'react'

import type { StreakBatchItem } from '../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../api/tasteQuizTypes'
import type { WatchingNowBatchItem } from '../api/watchPartyTypes'
import { useOptionalFeedAuthorBadges } from './useFeedAuthorBadges'
import { useRatingStreaksOfUsers } from './useRatingStreaksOfUsers'
import { useTasteQuizKnowledgeOfUsers } from './useTasteQuizKnowledgeOfUsers'
import { useWatchingNowOfUsers } from './useWatchingNowOfUsers'

type UseFeedCardAuthorBadgesArgs = {
  scopeKey: string
  tasteQuizOwnerIds: readonly string[]
  streakUserIds: readonly string[]
  panelCommentAuthorIds: readonly string[]
}

type FeedCardAuthorBadgesResult = {
  knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  watchingByUserId: Record<string, WatchingNowBatchItem>
}

/**
 * Uses page-level FeedAuthorBadgesProvider when present; falls back to local batch hooks elsewhere
 * (profile lists, post detail) so cards keep working without changing those pages.
 */
export function useFeedCardAuthorBadges({
  scopeKey,
  tasteQuizOwnerIds,
  streakUserIds,
  panelCommentAuthorIds,
}: UseFeedCardAuthorBadgesArgs): FeedCardAuthorBadgesResult {
  const providerBadges = useOptionalFeedAuthorBadges()

  const localTasteQuizOwnerIds = useMemo(
    () => [...new Set([...tasteQuizOwnerIds, ...panelCommentAuthorIds].filter((id) => id.trim() !== ''))].sort(),
    [panelCommentAuthorIds, tasteQuizOwnerIds],
  )
  const localStreakUserIds = useMemo(
    () => [...new Set([...streakUserIds, ...panelCommentAuthorIds].filter((id) => id.trim() !== ''))].sort(),
    [panelCommentAuthorIds, streakUserIds],
  )

  const { knowledgeByOwnerId: localKnowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(
    localTasteQuizOwnerIds,
    { enabled: providerBadges == null && localTasteQuizOwnerIds.length > 0 },
  )
  const { streakByUserId: localStreakByUserId } = useRatingStreaksOfUsers(localStreakUserIds, {
    enabled: providerBadges == null && localStreakUserIds.length > 0,
  })
  const { watchingByUserId: localWatchingByUserId } = useWatchingNowOfUsers(localStreakUserIds, {
    enabled: providerBadges == null && localStreakUserIds.length > 0,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  useEffect(() => {
    if (providerBadges == null) {
      return
    }
    providerBadges.registerCommentAuthors(scopeKey, panelCommentAuthorIds)
    return () => {
      providerBadges.registerCommentAuthors(scopeKey, [])
    }
  }, [panelCommentAuthorIds, providerBadges, scopeKey])

  if (providerBadges != null) {
    return {
      knowledgeByOwnerId: providerBadges.knowledgeByOwnerId,
      streakByUserId: providerBadges.streakByUserId,
      watchingByUserId: providerBadges.watchingByUserId,
    }
  }

  return {
    knowledgeByOwnerId: localKnowledgeByOwnerId,
    streakByUserId: localStreakByUserId,
    watchingByUserId: localWatchingByUserId,
  }
}
