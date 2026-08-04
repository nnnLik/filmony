import { createContext } from 'react'

import type { StreakBatchItem } from '../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../api/tasteQuizTypes'

export type FeedAuthorBadgesContextValue = {
  knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  registerCommentAuthors: (scopeKey: string, ids: readonly string[]) => void
}

export const FeedAuthorBadgesContext = createContext<FeedAuthorBadgesContextValue | null>(null)
