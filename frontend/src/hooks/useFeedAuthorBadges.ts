import { useContext } from 'react'

import {
  FeedAuthorBadgesContext,
  type FeedAuthorBadgesContextValue,
} from '../context/feedAuthorBadgesContext'

export function useFeedAuthorBadges(): FeedAuthorBadgesContextValue {
  const context = useContext(FeedAuthorBadgesContext)
  if (context == null) {
    throw new Error('useFeedAuthorBadges must be used within FeedAuthorBadgesProvider')
  }
  return context
}

export function useOptionalFeedAuthorBadges(): FeedAuthorBadgesContextValue | null {
  return useContext(FeedAuthorBadgesContext)
}
