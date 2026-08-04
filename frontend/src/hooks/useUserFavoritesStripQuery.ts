import { useQuery } from '@tanstack/react-query'

import { getUserCards } from '../api/profileApi'
import type { MovieCard } from '../api/profileTypes'
import { userFavoritesStripQueryKey } from '../lib/profileQueryKeys'

export type UseUserFavoritesStripQueryOptions = {
  enabled?: boolean
}

export function useUserFavoritesStripQuery(
  userId: string,
  options?: UseUserFavoritesStripQueryOptions,
) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useQuery<MovieCard[], Error>({
    queryKey: userFavoritesStripQueryKey(userId),
    queryFn: async () => {
      const page = await getUserCards(userId, { favoritesOnly: true, limit: 30 })
      return page.items
    },
    enabled,
    staleTime: 2 * 60_000,
    gcTime: 10 * 60_000,
  })
}
