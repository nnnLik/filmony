import type { SubscriptionListItem } from '../api/profileTypes'

/** Users who follow me and whom I follow (mutual subscriptions). */
export function filterMutualSubscriptions(items: SubscriptionListItem[]): SubscriptionListItem[] {
  const followerIds = new Set(
    items.filter((row) => row.relation_type === 'follower').map((row) => row.id),
  )
  const followingIds = new Set(
    items.filter((row) => row.relation_type === 'following').map((row) => row.id),
  )
  const mutualIds = new Set([...followerIds].filter((id) => followingIds.has(id)))
  const seen = new Set<string>()
  const out: SubscriptionListItem[] = []
  for (const row of items) {
    if (!mutualIds.has(row.id) || seen.has(row.id)) continue
    seen.add(row.id)
    out.push(row)
  }
  return out
}
