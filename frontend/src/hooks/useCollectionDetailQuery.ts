import { useQuery } from '@tanstack/react-query'

import { getCollectionBySlug } from '../api/collectionsApi'
import { collectionDetailQueryKey } from '../lib/collectionQueryKeys'
import { useAuthReadyGate } from './useAuthReadyGate'

export function useCollectionDetailQuery(slug: string) {
  const { isAuthReady } = useAuthReadyGate()

  return useQuery({
    queryKey: collectionDetailQueryKey(slug),
    queryFn: () => getCollectionBySlug(slug),
    enabled: isAuthReady && slug.trim() !== '',
    staleTime: 60_000,
  })
}
