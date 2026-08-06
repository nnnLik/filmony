import { useQuery } from '@tanstack/react-query'

import { listCollections } from '../api/collectionsApi'
import type { CollectionKind } from '../api/collectionsTypes'
import { collectionsListQueryKey } from '../lib/collectionQueryKeys'

import { useAuthReadyGate } from './useAuthReadyGate'

export function useCollectionsList(kind?: CollectionKind) {
  const { isAuthReady } = useAuthReadyGate()

  return useQuery({
    queryKey: collectionsListQueryKey(kind),
    queryFn: () => listCollections(kind != null ? { kind } : {}),
    enabled: isAuthReady,
    staleTime: 60_000,
  })
}
