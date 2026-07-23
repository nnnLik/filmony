import { useQuery } from '@tanstack/react-query'

import { checkTasteQuizCanPlay } from '../api/tasteQuizApi'
import type { TasteQuizCanPlayResponse } from '../api/tasteQuizTypes'
import { tasteQuizCanPlayQueryKey } from '../lib/tasteQuizQueryKeys'

export type UseTasteQuizCanPlayOptions = {
  enabled?: boolean
}

export function useTasteQuizCanPlay(
  ownerId: string | null | undefined,
  inviteToken?: string | null,
  options?: UseTasteQuizCanPlayOptions,
) {
  const enabled =
    (options?.enabled ?? true) && ownerId != null && ownerId.trim() !== ''

  return useQuery<TasteQuizCanPlayResponse, Error>({
    queryKey: tasteQuizCanPlayQueryKey(ownerId ?? '', inviteToken),
    queryFn: () => checkTasteQuizCanPlay(ownerId!.trim(), inviteToken),
    enabled,
  })
}
