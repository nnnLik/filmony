import { createContext } from 'react'

import type { OpenComposeFeedPostPayload } from './feedComposeTypes'

export type ComposeFeedPostContextValue = {
  openCompose: (payload?: OpenComposeFeedPostPayload) => void
  closeCompose: () => void
}

export const ComposeFeedPostContext = createContext<ComposeFeedPostContextValue | null>(null)
