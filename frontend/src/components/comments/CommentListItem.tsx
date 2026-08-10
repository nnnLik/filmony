import { Button } from '@telegram-apps/telegram-ui'
import type { MouseEventHandler, ReactNode } from 'react'

import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import type { ReactionSummary } from '../../api/profileTypes'
import { COMMENT_BODY_MAX_LEN } from '../../lib/commentReactionTokens'
import { commentAuthorLabel, snippetPreview } from '../../lib/commentDisplay'
import type { ThreadComment } from '../../lib/commentThreadTypes'
import { inlineMovieCardRefMapFromSnippets } from '../../lib/inlineMovieCardRefMap'
import { movieCardCommentDerivedFields } from '../../lib/movieCardCommentDerivedFields'
import { movieCardCommentImageSrc } from '../../lib/movieCardCommentMedia'
import { CommentBodyWithReactionTokens } from './CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from './CommentDraftMirrorField'
import { CommentHeaderActions } from './CommentHeaderActions'
import { CommentAuthorRow } from './CommentAuthorRow'
import { CommentParentQuote } from './CommentParentQuote'
import { ReactionStrip } from '../reactions/ReactionStrip'
import { FeedOpenableContainedImageThumbnail } from '../feed/FeedOpenableContainedImage'

export type CommentListItemLayout = 'detail' | 'feed'

export type CommentListItemProps = {
  comment: ThreadComment
  layout: CommentListItemLayout
  parent: ThreadComment | null
  parentCommentId: number | null
  highlighted?: boolean
  setCommentRef?: (element: HTMLDivElement | null) => void
  jumpBusy?: boolean
  onJumpToParent?: (parentCommentId: number) => void
  onReply?: () => void
  viewerId?: string | null
  knowledgeByAuthor?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  editingCommentId?: number | null
  editText?: string
  editBusy?: boolean
  onEditTextChange?: (value: string) => void
  onSaveEdit?: () => void
  onCancelEdit?: () => void
  onStartEdit?: () => void
  onDelete?: () => void
  onPublishToFeed?: () => void
  deleteCommentBusyId?: number | null
  reactionTargetKind: 'movie_card_comment' | 'feed_post_comment'
  reactionSummary?: ReactionSummary
  onReactionChange?: (next: ReactionSummary) => void
  detailHref?: string
  detailLinkState?: unknown
  onMouseDown?: MouseEventHandler
  replyControl?: ReactNode
}

export function CommentListItem({
  comment,
  layout,
  parent,
  parentCommentId,
  highlighted = false,
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
  reactionSummary,
  onReactionChange,
  detailHref,
  detailLinkState,
  onMouseDown,
  replyControl,
}: CommentListItemProps) {
  const isEditing = editingCommentId === comment.id
  const canManage = viewerId != null && comment.author.id === viewerId
  const derived =
    'image_url' in comment ? movieCardCommentDerivedFields(comment) : null

  const shellClass =
    layout === 'detail'
      ? `rounded-xl border bg-(--tgui--bg_color) p-3 motion-safe:transition-[border-color,box-shadow,transform] motion-safe:duration-300 ${
          highlighted
            ? 'border-(--tgui--link_color) shadow-[0_0_0_2px_color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] motion-safe:scale-[1.01]'
            : 'border-(--tgui--divider_color) motion-safe:hover:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,var(--tgui--divider_color))]'
        }`
      : 'rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2.5'

  const trailing =
    layout === 'feed' ? (
      replyControl ?? (
        <button
          type="button"
          className="shrink-0 py-0 text-xs leading-none text-(--tgui--link_color)"
          onMouseDown={onMouseDown}
          onClick={(e) => {
            e.stopPropagation()
            onReply?.()
          }}
        >
          Ответить
        </button>
      )
    ) : (
      <CommentHeaderActions
        onReply={() => onReply?.()}
        canManage={canManage}
        onEdit={canManage && onStartEdit != null ? onStartEdit : undefined}
        onDelete={canManage && onDelete != null ? onDelete : undefined}
        onPublishToFeed={canManage && onPublishToFeed != null ? onPublishToFeed : undefined}
        deleteBusy={deleteCommentBusyId === comment.id}
        disabled={editBusy && isEditing}
      />
    )

  const bodyTextClass = layout === 'detail' ? 'mt-1 text-sm leading-relaxed' : 'mt-1 text-[13px] leading-snug text-(--tgui--text_color)'

  return (
    <div
      ref={setCommentRef}
      className={shellClass}
      onMouseDown={onMouseDown}
    >
      <CommentAuthorRow
        author={comment.author}
        createdAt={comment.created_at}
        viewerId={viewerId}
        knowledgeByAuthor={knowledgeByAuthor}
        streakByUserId={streakByUserId}
        watchingByUserId={watchingByUserId}
        avatarSize={layout === 'feed' ? 24 : 28}
        nameAsLink={layout === 'detail'}
        trailing={trailing}
        onMouseDown={onMouseDown}
      />

      {parentCommentId != null ? (
        <div className={layout === 'feed' ? 'ms-8' : undefined}>
          <CommentParentQuote
            variant={onJumpToParent != null ? 'button' : 'link'}
            authorLabel={parent ? commentAuthorLabel(parent.author) : 'Родительский комментарий'}
            textPreview={
              parent
                ? snippetPreview(parent.text)
                : layout === 'feed'
                  ? 'Нажмите, чтобы перейти к родительскому комментарию'
                  : 'Нажмите, чтобы подгрузить и перейти'
            }
            disabled={jumpBusy}
            onActivate={() => onJumpToParent?.(parentCommentId)}
            href={detailHref}
            linkState={detailLinkState}
            onMouseDown={onMouseDown}
          />
        </div>
      ) : null}

      <div className={layout === 'feed' ? 'ms-8 min-w-0' : 'min-w-0'}>
        {isEditing ? (
          <div className="mt-1 space-y-2">
            <CommentDraftMultiline
              value={editText}
              onChange={(v) => onEditTextChange?.(v.slice(0, COMMENT_BODY_MAX_LEN))}
              placeholder="Редактировать комментарий"
              disabled={editBusy}
              rows={3}
            />
            <div className="flex gap-2">
              <Button
                size="s"
                disabled={
                  editBusy ||
                  (editText.trim() === '' &&
                    (derived == null || derived.imageSrc == null))
                }
                onClick={() => onSaveEdit?.()}
              >
                {editBusy ? 'Сохранение…' : 'Сохранить'}
              </Button>
              <Button size="s" mode="gray" disabled={editBusy} onClick={onCancelEdit}>
                Отмена
              </Button>
            </div>
          </div>
        ) : (
          <>
            {derived?.imageSrc != null ? (
              <FeedOpenableContainedImageThumbnail
                src={movieCardCommentImageSrc(derived.imageSrc)}
                wrapperClassName="mt-2 overflow-hidden rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)"
                imgClassName={
                  layout === 'feed'
                    ? 'max-h-[min(55vw,12rem)] w-full object-contain object-center bg-(--tgui--divider_color)'
                    : 'max-h-[min(60vw,16rem)] w-full object-contain object-center bg-(--tgui--divider_color)'
                }
              />
            ) : null}

            {(derived != null ? derived.textTrimmed !== '' : comment.text.trim() !== '') ? (
              <p className={bodyTextClass}>
                <CommentBodyWithReactionTokens
                  text={derived?.text ?? comment.text}
                  className="whitespace-pre-wrap"
                  inlineMovieCardRefs={inlineMovieCardRefMapFromSnippets(
                    derived?.referenced_movie_cards ?? comment.referenced_movie_cards,
                  )}
                  referencedMentions={derived?.referenced_mentions ?? comment.referenced_mentions}
                />
              </p>
            ) : null}
          </>
        )}

        <div
          className="mt-1.5 flex min-w-0 flex-nowrap items-center gap-x-1 overflow-hidden"
          onMouseDown={onMouseDown}
        >
          <ReactionStrip
            compact
            targetKind={reactionTargetKind}
            targetId={comment.id}
            summary={reactionSummary ?? comment.reactions}
            onSummaryChange={
              onReactionChange ??
              (() => {
                /* feed read-only reactions */
              })
            }
          />
        </div>
      </div>
    </div>
  )
}
