import type { FeedListMode } from '../api/profileTypes'

export const movieCardFeedQueryKey = (mode: FeedListMode) => ['movieCardFeed', mode] as const
