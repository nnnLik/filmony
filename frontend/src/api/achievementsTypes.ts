export type AchievementItem = {
  slug: string
  title: string
  description: string | null
  icon_key: string | null
  collection_slug: string
  unlocked: boolean
  unlocked_at: string | null
  holders_count: number
  eligible_users_count: number
  rarity_percent: number | null
  rarity_calculated_at: string | null
  is_pinned: boolean
  pin_slot_index: number | null
}

export type MyAchievementsListResponse = {
  items: AchievementItem[]
}

export type PinnedAchievement = {
  slug: string
  title: string
  description: string | null
  icon_key: string | null
  collection_slug: string
  unlocked_at: string
  holders_count: number
  eligible_users_count: number
  rarity_percent: number | null
  rarity_calculated_at: string | null
  slot_index: number
}

export type SetAchievementPinsRequest = {
  achievement_slugs: string[]
}
