import type { SubscriptionListItem } from '../api/profileTypes'

import type { MentionProfileRowInput } from './mentionProfileLookupUtils'

export function subscriptionToMentionRow(item: SubscriptionListItem): MentionProfileRowInput {
  return {
    id: item.id,
    profile_slug: item.profile_slug,
    username: item.username,
    display_name: item.display_name,
    first_name: item.first_name,
    last_name: item.last_name,
  }
}
