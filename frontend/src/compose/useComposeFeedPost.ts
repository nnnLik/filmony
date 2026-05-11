import { useContext } from 'react'

import { ComposeFeedPostContext } from './composeFeedPostContext'

export function useComposeFeedPost() {
  const ctx = useContext(ComposeFeedPostContext)
  if (ctx == null) {
    throw new Error('useComposeFeedPost must be used within ComposeFeedPostProvider')
  }
  return ctx
}
