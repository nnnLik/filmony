import type { StreakBatchItem } from '../../api/streaksTypes'

import { RatingStreakBadge } from './RatingStreakBadge'

export type RatingStreakAuthorBadgeProps = {
  /** User id → streak stats; use `useRatingStreaksOfUsers().streakByUserId`. */
  streakByUserId: Record<string, StreakBatchItem>
  authorId: string
  className?: string
}

export function RatingStreakAuthorBadge({
  streakByUserId,
  authorId,
  className,
}: RatingStreakAuthorBadgeProps) {
  const item = streakByUserId[authorId]
  if (item == null || item.current <= 3) {
    return null
  }
  return <RatingStreakBadge item={item} className={className} />
}
