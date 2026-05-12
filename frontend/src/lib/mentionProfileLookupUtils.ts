/** Данные для ссылки и подписи @… в тексте (ключ — `profile_slug` в нижнем регистре). */
export type MentionProfileRow = {
  userId: string
  username: string | null
  display_name: string | null
  first_name: string | null
  last_name: string | null
  /** Если задано (из `ReferencedMentionSnippet.display_label`), используется вместо вычисления по полям. */
  display_label?: string | null
}

export type MentionProfileRowInput = {
  id: string
  profile_slug: string
  username: string | null
  display_name?: string | null
  first_name?: string | null
  last_name?: string | null
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
    out.set(key, {
      userId: r.id,
      username: r.username,
      display_name: r.display_name ?? null,
      first_name: r.first_name ?? null,
      last_name: r.last_name ?? null,
    })
  }
  return out
}

export function authorLikeToMentionRow(a: {
  id: string
  profile_slug: string
  username: string | null
  first_name?: string | null
  last_name?: string | null
  display_name?: string | null
}): MentionProfileRowInput {
  return {
    id: a.id,
    profile_slug: a.profile_slug,
    username: a.username,
    display_name: a.display_name ?? null,
    first_name: a.first_name ?? null,
    last_name: a.last_name ?? null,
  }
}

export { mentionChipLabelFromRow } from './mentionChipDisplayLabel'
