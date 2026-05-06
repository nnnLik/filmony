import { useCallback } from 'react'

import { deleteMovieCard } from '../api/cardApi'

export function useRemoveMovieCard() {
  return useCallback(async (cardId: number) => {
    await deleteMovieCard(cardId)
  }, [])
}
