import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { batchTasteQuizKnowledge } from '../api/tasteQuizApi'
import type { TasteQuizKnowledgeBatchResponse } from '../api/tasteQuizTypes'
import { tasteQuizKnowledgeBatchQueryKey } from '../lib/tasteQuizQueryKeys'

export type UseTasteQuizKnowledgeBatchOptions = {
  enabled?: boolean
}

export function useTasteQuizKnowledgeBatch(
  ownerId: string | null | undefined,
  guesserUserIds: readonly string[],
  options?: UseTasteQuizKnowledgeBatchOptions,
) {
  const sortedIds = useMemo(
    () => [...new Set(guesserUserIds.filter((id) => id.trim() !== ''))].sort(),
    [guesserUserIds],
  )

  const enabled =
    (options?.enabled ?? true) &&
    ownerId != null &&
    ownerId.trim() !== '' &&
    sortedIds.length > 0

  return useQuery<TasteQuizKnowledgeBatchResponse, Error>({
    queryKey: tasteQuizKnowledgeBatchQueryKey(ownerId ?? '', sortedIds),
    queryFn: () => batchTasteQuizKnowledge(ownerId!.trim(), sortedIds),
    enabled,
  })
}
