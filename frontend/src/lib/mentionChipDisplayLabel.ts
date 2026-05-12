/**
 * Подпись @-чипа из полей строки профиля. Вынесено в отдельный модуль без связки с остальным
 * `mentionProfileLookupUtils`, чтобы type-aware ESLint не терял разрешение типа в компонентах ленты.
 */
export type MentionRowLikeForChipLabel = {
  display_label?: string | null
  display_name?: string | null
  first_name?: string | null
  last_name?: string | null
  username?: string | null
}

/** Текст чипа после «@»: имя/ФИО/username; slug только если профиля нет. */
export function mentionChipLabelFromRow(row: MentionRowLikeForChipLabel | undefined, slugLower: string): string {
  const api = row?.display_label?.trim()
  if (api) return api
  const dn = row?.display_name?.trim()
  if (dn) return dn
  const fl = [row?.first_name?.trim(), row?.last_name?.trim()].filter(Boolean).join(' ')
  if (fl) return fl
  const u = row?.username?.trim()
  if (u) return u.startsWith('@') ? u.slice(1) : u
  return slugLower
}
