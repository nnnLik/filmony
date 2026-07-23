import { useQuery } from '@tanstack/react-query'

import { getTasteQuizSession } from '../api/tasteQuizApi'
import type { TasteQuizSession } from '../api/tasteQuizTypes'
import { tasteQuizSessionQueryKey } from '../lib/tasteQuizQueryKeys'

export type UseTasteQuizSessionOptions = {
  enabled?: boolean
}

export function useTasteQuizSession(
  sessionId: string | null | undefined,
  options?: UseTasteQuizSessionOptions,
) {
  const enabled =
    (options?.enabled ?? true) && sessionId != null && sessionId.trim() !== ''

  return useQuery<TasteQuizSession, Error>({
    queryKey: tasteQuizSessionQueryKey(sessionId ?? ''),
    queryFn: () => getTasteQuizSession(sessionId!.trim()),
    enabled,
  })
}
