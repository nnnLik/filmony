import type {
  FeedPostComment,
  FeedPostCommentPage,
  MovieCardComment,
  MovieCardCommentPage,
  MovieCardCommentAuthor,
  ReactionSummary,
  ReferencedInlineMovieCardSnippet,
  ReferencedMentionSnippet,
} from '../api/profileTypes'

export type ThreadCommentAuthor = MovieCardCommentAuthor

/** Shared comment shape across movie-card and feed-post threads. */
export type ThreadCommentBase = {
  id: number
  parent_comment_id: number | null
  text: string
  created_at: string
  replies_count: number
  total_descendants_count: number
  author: ThreadCommentAuthor
  reactions?: ReactionSummary
  referenced_movie_cards?: ReferencedInlineMovieCardSnippet[]
  referenced_mentions?: ReferencedMentionSnippet[]
}

export type ThreadComment = FeedPostComment | MovieCardComment

export type CommentPage<T extends ThreadComment = ThreadComment> = {
  items: T[]
  next_cursor: string | null
}

export type ReplyToState = { id: number; label: string } | null

export type { FeedPostComment, FeedPostCommentPage, MovieCardComment, MovieCardCommentPage }
