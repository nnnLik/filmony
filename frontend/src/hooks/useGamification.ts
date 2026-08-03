import { useQuery } from '@tanstack/react-query'

import { getMyGamification, getUserGamificationPassport } from '../api/gamificationApi'
import type { GamificationResponse, PublicPassportResponse } from '../api/gamificationTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { myGamificationQueryKey, userPassportQueryKey } from '../lib/gamification/gamificationQueryKeys'

export type UseGamificationOptions = {
  enabled?: boolean
}

export function useGamification(options?: UseGamificationOptions) {
  const auth = useAuthStatus()
  const enabled = (options?.enabled ?? true) && auth.kind === 'ready'

  return useQuery<GamificationResponse, Error>({
    queryKey: myGamificationQueryKey(),
    queryFn: getMyGamification,
    enabled,
    staleTime: 5 * 60_000,
    gcTime: 30 * 60_000,
  })
}

export type UsePublicPassportOptions = {
  enabled?: boolean
}

export function usePublicPassport(userId: string, options?: UsePublicPassportOptions) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useQuery<PublicPassportResponse, Error>({
    queryKey: userPassportQueryKey(userId),
    queryFn: () => getUserGamificationPassport(userId),
    enabled,
    staleTime: 5 * 60_000,
    gcTime: 30 * 60_000,
  })
}
