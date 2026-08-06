import { useMutation, useQueryClient } from '@tanstack/react-query'

import { ApiError, formatApiDetail } from '../api/client'
import { pinCollection, unpinCollection } from '../api/collectionsApi'
import type { CollectionSummary } from '../api/collectionsTypes'
import {
  collectionDetailQueryKey,
  collectionsListQueryKey,
  profilePinnedCollectionsQueryKey,
} from '../lib/collectionQueryKeys'
import { useMyProfileQuery } from './useMyProfileQuery'

type PinMutationVariables = {
  slug: string
  nextPinned: boolean
}

export function useCollectionPinMutation() {
  const queryClient = useQueryClient()
  const myProfileQuery = useMyProfileQuery()
  const myUserId = myProfileQuery.data?.id ?? null

  return useMutation({
    mutationFn: async ({ slug, nextPinned }: PinMutationVariables) => {
      if (nextPinned) {
        await pinCollection(slug)
      } else {
        await unpinCollection(slug)
      }
    },
    onSuccess: (_data, { slug, nextPinned }) => {
      queryClient.setQueryData<CollectionSummary>(collectionDetailQueryKey(slug), (prev) => {
        if (prev == null) {
          return prev
        }
        return { ...prev, is_pinned: nextPinned }
      })

      void queryClient.invalidateQueries({ queryKey: collectionsListQueryKey() })
      void queryClient.invalidateQueries({ queryKey: collectionDetailQueryKey(slug) })

      if (myUserId != null) {
        void queryClient.invalidateQueries({
          queryKey: profilePinnedCollectionsQueryKey(myUserId),
        })
      }
    },
  })
}

export function formatCollectionPinError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) {
      return 'Можно закрепить не больше 10 коллекций'
    }
    return formatApiDetail(error.detail)
  }
  return error instanceof Error ? error.message : 'Не удалось обновить закрепление'
}
