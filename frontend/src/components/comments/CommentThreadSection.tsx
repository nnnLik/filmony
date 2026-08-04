import type { ChangeEvent, Dispatch, KeyboardEventHandler, RefObject, SetStateAction } from 'react'

import type { WatchedInlinePickerItem } from '../../api/watchedInlinePickerTypes'
import type { SubscriptionListItem } from '../../api/profileTypes'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { ThreadComment, ReplyToState } from '../../lib/commentThreadTypes'
import type { ActiveMentionQuery } from '../../lib/feedMentionCompose'
import { commentAuthorLabel } from '../../lib/commentDisplay'
import { PlayfulHint } from '../ui/PlayfulHint'
import { CommentComposeBar } from './CommentComposeBar'
import { CommentThreadList } from './CommentThreadList'

export type CommentThreadSectionProps<T extends ThreadComment> = {
  comments: T[]
  commentsById: Map<number, T>
  commentsLoading: boolean
  commentsError: string | null
  commentsNextCursor: string | null
  loadComments: (append: boolean) => Promise<void>
  replyTo: ReplyToState
  setReplyTo: Dispatch<SetStateAction<ReplyToState>>
  viewerId: string | null
  submitBusy: boolean
  jumpBusy: boolean
  highlightCommentId: number | null
  setCommentRef: (commentId: number, element: HTMLDivElement | null) => void
  handleJumpToParent: (parentCommentId: number) => Promise<void>
  handleCreateComment: () => Promise<void>
  commentText: string
  onCommentTextChange: (value: string, meta?: { caret: number }) => void
  onCommentKeyDown: KeyboardEventHandler<HTMLTextAreaElement>
  onCommentKeyUp: () => void
  onCommentSelect: () => void
  commentTextAreaRef: RefObject<HTMLTextAreaElement | null>
  commentDraftInlineCardRefs: ReadonlyMap<number, { film_title: string; film_year: number | null }>
  insertReactionIntoComment: (reactionTypeId: number) => void
  toggleSpoilerInComment: () => void
  insertMovieCardIntoComment: (row: WatchedInlinePickerItem) => void
  charsLeft: number
  commentMentionAnchorRef: RefObject<HTMLDivElement | null>
  commentMentionPicker: ActiveMentionQuery | null
  commentMentionHighlightIdx: number
  commentMentionFiltered: SubscriptionListItem[]
  commentMentionPopoverLayout: { top: number; left: number; width: number; maxHeight: number } | null
  followingMentionItems: SubscriptionListItem[]
  followingMentionQueryPending: boolean
  followingMentionQueryError: boolean
  onPickCommentMention: (slug: string) => void
  onDismissCommentMention: () => void
  tasteQuizKnowledgeByAuthor: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  editingCommentId: number | null
  editText: string
  setEditText: Dispatch<SetStateAction<string>>
  editBusy: boolean
  deleteCommentBusyId: number | null
  onStartEditComment: (comment: T) => void
  onCancelEditComment: () => void
  onSaveEditComment: (comment: T) => void
  onDeleteComment: (commentId: number) => void
  setComments: Dispatch<SetStateAction<T[]>>
  reactionTargetKind: 'movie_card_comment' | 'feed_post_comment'
  commentImageUrl?: string | null
  setCommentImageUrl?: Dispatch<SetStateAction<string | null>>
  commentImageUploadBusy?: boolean
  commentImageFileInputRef?: RefObject<HTMLInputElement | null>
  handlePickCommentImage?: () => void
  handleCommentImageFileChange?: (event: ChangeEvent<HTMLInputElement>) => void
  onPublishToFeed?: (comment: T) => void
  sectionClassName?: string
  showSectionTitle?: boolean
}

export function CommentThreadSection<T extends ThreadComment>({
  comments,
  commentsById,
  commentsLoading,
  commentsError,
  commentsNextCursor,
  loadComments,
  replyTo,
  setReplyTo,
  viewerId,
  submitBusy,
  jumpBusy,
  highlightCommentId,
  setCommentRef,
  handleJumpToParent,
  handleCreateComment,
  commentText,
  onCommentTextChange,
  onCommentKeyDown,
  onCommentKeyUp,
  onCommentSelect,
  commentTextAreaRef,
  commentDraftInlineCardRefs,
  insertReactionIntoComment,
  toggleSpoilerInComment,
  insertMovieCardIntoComment,
  charsLeft,
  commentMentionAnchorRef,
  commentMentionPicker,
  commentMentionHighlightIdx,
  commentMentionFiltered,
  commentMentionPopoverLayout,
  followingMentionItems,
  followingMentionQueryPending,
  followingMentionQueryError,
  onPickCommentMention,
  onDismissCommentMention,
  tasteQuizKnowledgeByAuthor,
  streakByUserId,
  editingCommentId,
  editText,
  setEditText,
  editBusy,
  deleteCommentBusyId,
  onStartEditComment,
  onCancelEditComment,
  onSaveEditComment,
  onDeleteComment,
  setComments,
  reactionTargetKind,
  commentImageUrl = null,
  setCommentImageUrl,
  commentImageUploadBusy = false,
  commentImageFileInputRef,
  handlePickCommentImage,
  handleCommentImageFileChange,
  onPublishToFeed,
  sectionClassName = 'filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-3 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4',
  showSectionTitle = true,
}: CommentThreadSectionProps<T>) {
  return (
    <section className={sectionClassName}>
      {showSectionTitle ? (
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Комментарии</p>
      ) : null}

      {replyTo != null ? (
        <div className="mt-2 flex items-center justify-between rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,var(--tgui--divider_color))] bg-(--tgui--bg_color) px-3 py-2 text-xs motion-safe:animate-[filmony-detail-fade-in_0.25s_ease-out_both]">
          <span className="text-(--tgui--hint_color)">Ответ для: {replyTo.label}</span>
          <button type="button" onClick={() => setReplyTo(null)} className="text-(--tgui--link_color)">
            отменить
          </button>
        </div>
      ) : null}

      <CommentComposeBar
        mode="multiline"
        value={commentText}
        onChange={onCommentTextChange}
        onSubmit={() => void handleCreateComment()}
        submitBusy={submitBusy}
        disabled={commentImageUploadBusy}
        charsLeft={charsLeft}
        submitError={null}
        placeholder="Напишите комментарий..."
        inlineMovieCardRefs={commentDraftInlineCardRefs}
        onKeyDown={onCommentKeyDown}
        onKeyUp={onCommentKeyUp}
        onSelect={onCommentSelect}
        textareaRef={commentTextAreaRef}
        onInsertReaction={insertReactionIntoComment}
        onToggleSpoiler={toggleSpoilerInComment}
        onInsertMovieCard={insertMovieCardIntoComment}
        mentionAnchorRef={commentMentionAnchorRef}
        mentionPicker={commentMentionPicker}
        mentionHighlightIdx={commentMentionHighlightIdx}
        mentionFiltered={commentMentionFiltered}
        mentionPopoverLayout={commentMentionPopoverLayout}
        followingMentionQueryPending={followingMentionQueryPending}
        followingMentionQueryError={followingMentionQueryError}
        followingMentionItemsCount={followingMentionItems.length}
        onPickMention={onPickCommentMention}
        onDismissMention={onDismissCommentMention}
        imageUrl={commentImageUrl}
        imageUploadBusy={commentImageUploadBusy}
        onPickImage={handlePickCommentImage}
        onClearImage={setCommentImageUrl != null ? () => setCommentImageUrl(null) : undefined}
        imageFileInputRef={commentImageFileInputRef}
        onImageFileChange={handleCommentImageFileChange}
      />

      {commentsError != null ? (
        <p className="mt-2 text-sm text-(--tgui--destructive_text_color)">{commentsError}</p>
      ) : null}

      {commentsLoading ? (
        <p className="mt-3 text-sm text-(--tgui--hint_color)">Загрузка комментариев…</p>
      ) : null}

      {!commentsLoading && comments.length === 0 ? (
        <PlayfulHint
          poolKey="comments_empty"
          fallback="Пока нет комментариев. Будьте первым."
          userId={viewerId}
          className="mt-3 text-sm text-(--tgui--hint_color)"
        />
      ) : null}

      {comments.length > 0 ? (
        <div className="mt-3">
          <CommentThreadList
            comments={comments}
            commentsById={commentsById}
            layout="detail"
            highlightCommentId={highlightCommentId}
            setCommentRef={setCommentRef}
            jumpBusy={jumpBusy}
            onJumpToParent={(parentId) => void handleJumpToParent(parentId)}
            onReply={(comment) =>
              setReplyTo({ id: comment.id, label: commentAuthorLabel(comment.author) })
            }
            viewerId={viewerId}
            knowledgeByAuthor={tasteQuizKnowledgeByAuthor}
            streakByUserId={streakByUserId}
            editingCommentId={editingCommentId}
            editText={editText}
            editBusy={editBusy}
            onEditTextChange={setEditText}
            onSaveEdit={onSaveEditComment}
            onCancelEdit={onCancelEditComment}
            onStartEdit={(comment) => {
              onStartEditComment(comment)
              setReplyTo(null)
            }}
            onDelete={onDeleteComment}
            onPublishToFeed={onPublishToFeed}
            deleteCommentBusyId={deleteCommentBusyId}
            reactionTargetKind={reactionTargetKind}
            onReactionChange={(commentId, next) =>
              setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, reactions: next } : c)))
            }
            listClassName="space-y-2"
          />
        </div>
      ) : null}

      {commentsNextCursor ? (
        <button
          type="button"
          onClick={() => void loadComments(true)}
          className="mt-3 text-xs text-(--tgui--link_color)"
          disabled={commentsLoading}
        >
          Показать еще комментарии
        </button>
      ) : null}
    </section>
  )
}
