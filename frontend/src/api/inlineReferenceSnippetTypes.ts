/**
 * DTO для токенов ⟦c{id}⟧ и ⟦@slug⟧ в телах комментариев/постов.
 * Отдельный модуль без зависимостей — разрывает цикл `profileTypes` ↔ `feedInFeedTypes`
 * для type-aware ESLint и IDE.
 */

export type ReferencedInlineMovieCardSnippet = {
  movie_card_id: number
  film_title: string
  film_year: number | null
}

export type ReferencedMentionSnippet = {
  user_id: string
  profile_slug: string
  /** Подпись чипа с сервера (как `mentionChipLabelFromRow`). */
  display_label: string
  username: string | null
  display_name: string | null
  first_name: string | null
  last_name: string | null
}
