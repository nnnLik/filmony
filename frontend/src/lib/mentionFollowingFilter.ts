import type { SubscriptionListItem } from '../api/profileTypes'

export function filterFollowingForMentionQuery(
  items: SubscriptionListItem[],
  query: string,
): SubscriptionListItem[] {
  const n = query.trim().toLowerCase()
  if (n === '') {
    return items
  }
  return items.filter((it) => {
    const slug = it.profile_slug.toLowerCase()
    const dn = (it.display_name ?? '').toLowerCase()
    const un = (it.username ?? '').toLowerCase()
    return slug.startsWith(n) || dn.includes(n) || un.includes(n)
  })
}
