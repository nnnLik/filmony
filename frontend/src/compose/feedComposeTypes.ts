import type { ReferencedInlineMovieCardSnippet, ReferencedMentionSnippet } from '../api/inlineReferenceSnippetTypes'

export type OpenComposeFeedPostPayload = {
  sourceCommentId?: number | null
  referencedMovieCardId?: number | null
  /** Картинка комментария при «В ленту» — в пост переносится без возможности сменить */
  sourceCommentImageUrl?: string | null
  /** Только превью в композере; в API тело поста не подставляется из комментария */
  sourceCommentPreviewAuthorLabel?: string | null
  sourceCommentPreviewText?: string | null
  sourceCommentReferencedMovieCards?: ReferencedInlineMovieCardSnippet[] | null
  sourceCommentReferencedMentions?: ReferencedMentionSnippet[] | null
}

/** Снимок комментария только для UI композера «В ленту». */
export type FeedComposeSourceCommentPreview = {
  authorLabel: string
  text: string
  referencedMovieCards: ReferencedInlineMovieCardSnippet[] | undefined
  referencedMentions: ReferencedMentionSnippet[] | undefined
}
