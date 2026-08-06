import type { AchievementItem } from '../api/achievementsTypes'

export function formatAchievementRarity(item: {
  rarity_percent: number | null
  holders_count: number
}): string {
  if (item.rarity_percent == null) {
    return '—'
  }
  const percent =
    item.rarity_percent >= 0.1
      ? item.rarity_percent.toFixed(1)
      : item.rarity_percent.toFixed(2)
  return `${percent}% · ${item.holders_count}`
}

export function sortedAchievements(items: readonly AchievementItem[]): AchievementItem[] {
  return [...items].sort((a: AchievementItem, b: AchievementItem) => {
    if (a.unlocked !== b.unlocked) {
      return a.unlocked ? -1 : 1
    }
    if (a.unlocked && b.unlocked) {
      const aTime = a.unlocked_at ?? ''
      const bTime = b.unlocked_at ?? ''
      return bTime.localeCompare(aTime)
    }
    return a.title.localeCompare(b.title, 'ru')
  })
}

export function pinnedSlugsFromAchievements(items: readonly AchievementItem[]): string[] {
  return items
    .filter((item) => item.is_pinned && item.pin_slot_index != null)
    .sort((a, b) => (a.pin_slot_index ?? 0) - (b.pin_slot_index ?? 0))
    .map((item) => item.slug)
}
