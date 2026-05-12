export type OpenComposeFeedPostPayload = {
  sourceCommentId?: number | null
  referencedMovieCardId?: number | null
  /** Картинка комментария при «В ленту» — в пост переносится без возможности сменить */
  sourceCommentImageUrl?: string | null
}
