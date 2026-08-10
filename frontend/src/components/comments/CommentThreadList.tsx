import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import type { ReactionSummary } from '../../api/profileTypes'
import type { ThreadComment } from '../../lib/commentThreadTypes'
import { CommentListItem, type CommentListItemLayout } from './CommentListItem'

export type CommentThreadListProps<T extends ThreadComment> = {
  comments: T[]
  commentsById: Map<number, T>
  layout: CommentListItemLayout
  highlightCommentId?: number | null
  setCommentRef?: (commentId: number, element: HTMLDivElement | null) => void
  jumpBusy?: boolean
  onJumpToParent?: (parentCommentId: number) => void
  onReply?: (comment: T) => void
  viewerId?: string | null
  knowledgeByAuthor?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  editingCommentId?: number | null
  editText?: string
  editBusy?: boolean
  onEditTextChange?: (value: string) => void
  onSaveEdit?: (comment: T) => void
  onCancelEdit?: () => void
  onStartEdit?: (comment: T) => void
  onDelete?: (commentId: number) => void
  onPublishToFeed?: (comment: T) => void
  deleteCommentBusyId?: number | null
  reactionTargetKind: 'movie_card_comment' | 'feed_post_comment'
  previewReactions?: Record<number, ReactionSummary>
  onPreviewReactionChange?: (commentId: number, next: ReactionSummary) => void
  onReactionChange?: (commentId: number, next: ReactionSummary) => void
  detailHref?: string
  detailLinkState?: unknown
  onMouseDown?: React.MouseEventHandler
  listClassName?: string
}

export function CommentThreadList<T extends ThreadComment>({
  comments,
  commentsById,
  layout,
  highlightCommentId = null,
  setCommentRef,
  jumpBusy = false,
  onJumpToParent,
  onReply,
  viewerId = null,
  knowledgeByAuthor,
  streakByUserId,
  watchingByUserId,
  editingCommentId = null,
  editText = '',
  editBusy = false,
  onEditTextChange,
  onSaveEdit,
  onCancelEdit,
  onStartEdit,
  onDelete,
  onPublishToFeed,
  deleteCommentBusyId = null,
  reactionTargetKind,
  previewReactions,
  onPreviewReactionChange,
  onReactionChange,
  detailHref,
  detailLinkState,
  onMouseDown,
  listClassName = 'space-y-1.5',
}: CommentThreadListProps<T>) {
  return (
    <div className={listClassName}>
      {comments.map((comment) => {
        const parentCommentId = comment.parent_comment_id
        const parent =
          parentCommentId != null ? commentsById.get(parentCommentId) ?? null : null
        return (
          <CommentListItem
            key={comment.id}
            comment={comment}
            layout={layout}
            parent={parent}
            parentCommentId={parentCommentId}
            highlighted={highlightCommentId === comment.id}
            setCommentRef={
              setCommentRef != null
                ? (element) => {
                    setCommentRef(comment.id, element)
                  }
                : undefined
            }
            jumpBusy={jumpBusy}
            onJumpToParent={onJumpToParent}
            onReply={() => onReply?.(comment)}
            viewerId={viewerId}
            knowledgeByAuthor={knowledgeByAuthor}
            streakByUserId={streakByUserId}
            watchingByUserId={watchingByUserId}
            editingCommentId={editingCommentId}
            editText={editText}
            editBusy={editBusy}
            onEditTextChange={onEditTextChange}
            onSaveEdit={() => onSaveEdit?.(comment)}
            onCancelEdit={onCancelEdit}
            onStartEdit={() => onStartEdit?.(comment)}
            onDelete={() => onDelete?.(comment.id)}
            onPublishToFeed={() => onPublishToFeed?.(comment)}
            deleteCommentBusyId={deleteCommentBusyId}
            reactionTargetKind={reactionTargetKind}
            reactionSummary={previewReactions?.[comment.id]}
            onReactionChange={
              onPreviewReactionChange != null
                ? (next) => {
                    onPreviewReactionChange(comment.id, next)
                  }
                : onReactionChange != null
                  ? (next) => {
                      onReactionChange(comment.id, next)
                    }
                  : undefined
            }
            detailHref={detailHref}
            detailLinkState={detailLinkState}
            onMouseDown={onMouseDown}
          />
        )
      })}
    </div>
  )
}
