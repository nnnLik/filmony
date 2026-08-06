import { useQuery } from '@tanstack/react-query'

import { getProfilePinnedCollections } from '../api/collectionsApi'
import { profilePinnedCollectionsQueryKey } from '../lib/collectionQueryKeys'
import { useAuthReadyGate } from './useAuthReadyGate'

export function useProfilePinnedCollectionsQuery(userId: string) {
  const { isAuthReady } = useAuthReadyGate()

  return useQuery({
    queryKey: profilePinnedCollectionsQueryKey(userId),
    queryFn: () => getProfilePinnedCollections(userId),
    enabled: isAuthReady && userId.trim() !== '',
    staleTime: 60_000,
  })
}
