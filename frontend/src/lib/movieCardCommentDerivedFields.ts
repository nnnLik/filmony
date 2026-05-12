import type { ReferencedInlineMovieCardSnippet, ReferencedMentionSnippet } from '../api/inlineReferenceSnippetTypes'

/**
 * Минимальный срез полей комментария для превью. Не используем `MovieCardComment` из `profileTypes`, чтобы
 * type-aware ESLint не видел на полях `error` из-за тяжёлого графа импортов.
 */
export type MovieCardCommentDerivedSource = {
  id: number
  text: string
  image_url?: string | null
  referenced_movie_cards?: ReferencedInlineMovieCardSnippet[] | null
  referenced_mentions?: ReferencedMentionSnippet[] | null
}

/**
 * Производные поля комментария карточки (превью картинки, текст, вставки) без импорта тяжёлого `cardApi`,
 * чтобы IDE/ESLint не помечали обращения к полям как `error` в странице детали.
 */
export function movieCardCommentDerivedFields(comment: MovieCardCommentDerivedSource): {
  id: number
  sourceCommentImageUrl: string | null
  text: string
  textTrimmed: string
  imageSrc: string | null
  referenced_movie_cards: ReferencedInlineMovieCardSnippet[] | undefined
  referenced_mentions: ReferencedMentionSnippet[] | undefined
} {
  const rawImage = comment.image_url
  const imageSrc = typeof rawImage === 'string' && rawImage.trim() !== '' ? rawImage : null
  const text = comment.text
  return {
    id: comment.id,
    sourceCommentImageUrl: comment.image_url ?? null,
    text,
    textTrimmed: text.trim(),
    imageSrc,
    referenced_movie_cards: comment.referenced_movie_cards ?? undefined,
    referenced_mentions: comment.referenced_mentions ?? undefined,
  }
}
