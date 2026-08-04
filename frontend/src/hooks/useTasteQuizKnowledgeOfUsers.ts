import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { batchTasteQuizKnowledgeAsGuesser } from '../api/tasteQuizApi'
import {
  TASTE_QUIZ_KNOWLEDGE_BATCH_MAX_OWNER_IDS,
  type TasteQuizKnowledgeBatchItem,
  type TasteQuizKnowledgeBatchResponse,
} from '../api/tasteQuizTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { tasteQuizKnowledgeOfUsersQueryKey } from '../lib/tasteQuizQueryKeys'

export type UseTasteQuizKnowledgeOfUsersOptions = {
  enabled?: boolean
  staleTime?: number
  gcTime?: number
}

function normalizeOwnerUserIds(ownerUserIds: readonly string[]): string[] {
  const unique = [...new Set(ownerUserIds.filter((id) => id.trim() !== ''))]
  return unique.slice(0, TASTE_QUIZ_KNOWLEDGE_BATCH_MAX_OWNER_IDS).sort()
}

/**
 * Batch knowledge from the authenticated viewer's perspective: how well they know each owner.
 *
 * Return shape: `knowledgeByOwnerId` maps owner user id → `{ attempts, accuracy_pct, points_sum }`.
 */
export function useTasteQuizKnowledgeOfUsers(
  ownerUserIds: readonly string[],
  options?: UseTasteQuizKnowledgeOfUsersOptions,
) {
  const auth = useAuthStatus()
  const sortedIds = useMemo(() => normalizeOwnerUserIds(ownerUserIds), [ownerUserIds])

  const enabled =
    (options?.enabled ?? true) && auth.kind === 'ready' && sortedIds.length > 0

  const query = useQuery<TasteQuizKnowledgeBatchResponse, Error>({
    queryKey: tasteQuizKnowledgeOfUsersQueryKey(sortedIds),
    queryFn: () => batchTasteQuizKnowledgeAsGuesser(sortedIds),
    enabled,
    ...(options?.staleTime != null ? { staleTime: options.staleTime } : {}),
    ...(options?.gcTime != null ? { gcTime: options.gcTime } : {}),
  })

  const knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem> =
    query.data?.items ?? {}

  return {
    ...query,
    knowledgeByOwnerId,
  }
}
