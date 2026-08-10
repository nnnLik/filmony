import { createContext } from 'react'

import type { StreakBatchItem } from '../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../api/tasteQuizTypes'
import type { WatchingNowBatchItem } from '../api/watchPartyTypes'

export type FeedAuthorBadgesContextValue = {
  knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  watchingByUserId: Record<string, WatchingNowBatchItem>
  registerCommentAuthors: (scopeKey: string, ids: readonly string[]) => void
}

export const FeedAuthorBadgesContext = createContext<FeedAuthorBadgesContextValue | null>(null)
