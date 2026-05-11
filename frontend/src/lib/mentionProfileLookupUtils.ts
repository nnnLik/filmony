import type { SubscriptionListItem } from '../api/profileTypes'

/** Данные для ссылки и подписи @… в тексте (ключ — `profile_slug` в нижнем регистре). */
export type MentionProfileRow = {
  userId: string
  username: string | null
}

export type MentionProfileRowInput = {
  id: string
  profile_slug: string
  username: string | null
}

export function mentionProfileKeyFromSlug(slug: string): string {
  return slug.trim().toLowerCase()
}

export function mergeMentionProfileMaps(
  parent: ReadonlyMap<string, MentionProfileRow> | undefined,
  rows: readonly MentionProfileRowInput[],
): ReadonlyMap<string, MentionProfileRow> {
  const out = new Map<string, MentionProfileRow>(parent ?? [])
  for (const r of rows) {
    const key = mentionProfileKeyFromSlug(r.profile_slug)
    if (key.length === 0) continue
    out.set(key, { userId: r.id, username: r.username })
  }
  return out
}

export function authorLikeToMentionRow(a: {
  id: string
  profile_slug: string
  username: string | null
}): MentionProfileRowInput {
  return { id: a.id, profile_slug: a.profile_slug, username: a.username }
}

export function subscriptionToMentionRow(item: SubscriptionListItem): MentionProfileRowInput {
  return { id: item.id, profile_slug: item.profile_slug, username: item.username }
}

/** Что показываем после «@»: username без ведущего @, иначе slug. */
export function mentionHandleForDisplay(username: string | null | undefined, slugLower: string): string {
  const u = username?.trim()
  if (u != null && u !== '') {
    return u.startsWith('@') ? u.slice(1) : u
  }
  return slugLower
}
