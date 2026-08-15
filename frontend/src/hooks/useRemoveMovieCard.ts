import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'

import { deleteMovieCard } from '../api/cardApi'
import { invalidateProfileAggregates } from '../lib/invalidateProfileAggregates'

export function useRemoveMovieCard() {
  const queryClient = useQueryClient()

  return useCallback(async (cardId: number) => {
    await deleteMovieCard(cardId)
    invalidateProfileAggregates(queryClient)
  }, [queryClient])
}
