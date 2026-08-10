import { Link } from 'react-router'
import type { MouseEventHandler, RefObject } from 'react'

import type { ReactionSummary } from '../../api/profileTypes'
import type { ThreadComment } from '../../lib/commentThreadTypes'
import { PlayfulHint } from '../ui/PlayfulHint'
import { ReactionStrip } from '../reactions/ReactionStrip'
import { IconChevronDown } from './FeedCardIcons'
import { CommentThreadList } from '../comments/CommentThreadList'
import { CommentComposeBar } from '../comments/CommentComposeBar'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import type { WatchedInlinePickerItem } from '../../api/watchedInlinePickerTypes'

export type EngagementCommentsRowProps<T extends ThreadComment> = {
  commentsCount: number
  commentsPreviewOpen: boolean
  onTogglePreview: () => void
  reactionTargetKind: 'movie_card' | 'feed_post'
  reactionTargetId: number
  reactionSummary?: ReactionSummary
  onReactionChange: (next: ReactionSummary) => void
  panelComments: T[]
  previewCommentsById: Map<number, T>
  panelLoading: boolean
  panelError: string | null
  detailHref: string
  detailLinkState?: unknown
  viewerUserId?: string | null
  knowledgeByAuthor?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  previewReactions?: Record<number, ReactionSummary>
  onPreviewReactionChange?: (commentId: number, next: ReactionSummary) => void
  commentReactionTargetKind: 'movie_card_comment' | 'feed_post_comment'
  setCommentRef?: (commentId: number, element: HTMLDivElement | null) => void
  highlightCommentId?: number | null
  onJumpToParent?: (parentCommentId: number) => void
  onReply?: (comment: T) => void
  draft: string
  onDraftChange: (value: string) => void
  draftInputRef?: RefObject<HTMLInputElement | null>
  draftInlineCardRefs?: ReadonlyMap<number, { film_title: string; film_year: number | null }>
  onDraftKeyDown?: React.KeyboardEventHandler<HTMLInputElement>
  onInsertReaction?: (reactionTypeId: number) => void
  onToggleSpoiler?: () => void
  onInsertMovieCard?: (row: WatchedInlinePickerItem) => void
  onSubmit: () => void
  submitBusy?: boolean
  submitError?: string | null
  charsLeft: number
  stopNav?: MouseEventHandler
  stopNavKeepFocus?: MouseEventHandler
  stopNavClick?: MouseEventHandler
  linkToDetail?: boolean
  detailFallbackLabel?: string
  inlineCommentsEnabled?: boolean
}

export function EngagementCommentsRow<T extends ThreadComment>({
  commentsCount,
  commentsPreviewOpen,
  onTogglePreview,
  reactionTargetKind,
  reactionTargetId,
  reactionSummary,
  onReactionChange,
  panelComments,
  previewCommentsById,
  panelLoading,
  panelError,
  detailHref,
  detailLinkState,
  viewerUserId = null,
  knowledgeByAuthor,
  streakByUserId,
  watchingByUserId,
  previewReactions,
  onPreviewReactionChange,
  commentReactionTargetKind,
  setCommentRef,
  highlightCommentId = null,
  onJumpToParent,
  onReply,
  draft,
  onDraftChange,
  draftInputRef,
  draftInlineCardRefs,
  onDraftKeyDown,
  onInsertReaction,
  onToggleSpoiler,
  onInsertMovieCard,
  onSubmit,
  submitBusy = false,
  submitError = null,
  charsLeft,
  stopNav,
  stopNavKeepFocus,
  stopNavClick,
  linkToDetail = false,
  detailFallbackLabel = 'Открыть',
  inlineCommentsEnabled = true,
}: EngagementCommentsRowProps<T>) {
  return (
    <div
      className="relative z-10 flex min-w-0 flex-col gap-1.5"
      onClick={linkToDetail ? stopNavClick : undefined}
    >
      <div className="flex min-w-0 items-center justify-between gap-2">
        <div
          className="min-w-0 flex-1 overflow-hidden py-px"
          onMouseDown={linkToDetail ? stopNav : undefined}
          onClick={linkToDetail ? stopNavClick : undefined}
        >
          <ReactionStrip
            targetKind={reactionTargetKind}
            targetId={reactionTargetId}
            summary={reactionSummary}
            onSummaryChange={onReactionChange}
            compact
          />
        </div>
        {inlineCommentsEnabled ? (
          <div
            className="flex shrink-0 items-center gap-1 border-l border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] pl-2"
            onMouseDown={linkToDetail ? stopNav : undefined}
            onClick={linkToDetail ? stopNavClick : undefined}
          >
          <span
            title="Комментарии"
            className="max-w-22 truncate text-[11px] font-medium leading-none text-(--tgui--hint_color) sm:max-w-none"
          >
            Комментарии
          </span>
          <span
            className="text-xs font-semibold tabular-nums leading-none text-(--tgui--text_color)"
            title="Всего комментариев"
          >
            {commentsCount}
          </span>
          <button
            type="button"
            onMouseDown={linkToDetail ? stopNav : undefined}
            onClick={(e) => {
              if (linkToDetail) stopNavClick?.(e)
              onTogglePreview()
            }}
            aria-expanded={commentsPreviewOpen}
            aria-label={
              commentsPreviewOpen
                ? 'Скрыть список комментариев и поле ввода'
                : 'Показать комментарии и написать ответ'
            }
            className="flex size-7 shrink-0 items-center justify-center rounded-md text-(--tgui--hint_color) transition-[background-color,color,transform] hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] hover:text-(--tgui--text_color) active:scale-95"
          >
            <IconChevronDown
              className={`size-4 transition-transform duration-200 ${commentsPreviewOpen ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
        ) : null}
      </div>

      {inlineCommentsEnabled && commentsPreviewOpen ? (
        <div
          className="flex flex-col gap-2 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_55%,transparent)] pt-2"
          onClick={linkToDetail ? stopNavClick : undefined}
        >
          {commentsCount > 0 ? (
            <div
              className="max-h-[min(42vh,15rem)] min-h-30 overflow-y-auto overscroll-y-contain touch-pan-y pr-0.5 [-webkit-overflow-scrolling:touch]"
              role="region"
              aria-label="Комментарии"
            >
              {panelLoading ? (
                <p className="py-6 text-center text-xs text-(--tgui--hint_color)">Загрузка…</p>
              ) : panelError != null ? (
                <p className="text-xs text-(--tgui--destructive_text_color,#ef4444)">
                  {panelError}{' '}
                  <Link
                    to={detailHref}
                    state={detailLinkState}
                    className="text-(--tgui--link_color) no-underline active:opacity-90"
                  >
                    {detailFallbackLabel}
                  </Link>
                </p>
              ) : panelComments.length === 0 ? (
                <p className="text-xs text-(--tgui--hint_color)">
                  <Link
                    to={detailHref}
                    state={detailLinkState}
                    className="text-(--tgui--link_color) no-underline active:opacity-90"
                  >
                    {detailFallbackLabel}
                  </Link>
                  , чтобы прочитать комментарии.
                </p>
              ) : (
                <CommentThreadList
                  comments={panelComments}
                  commentsById={previewCommentsById}
                  layout="feed"
                  highlightCommentId={highlightCommentId}
                  setCommentRef={setCommentRef}
                  onJumpToParent={onJumpToParent}
                  onReply={onReply}
                  viewerId={viewerUserId}
                  knowledgeByAuthor={knowledgeByAuthor}
                  streakByUserId={streakByUserId}
                  watchingByUserId={watchingByUserId}
                  reactionTargetKind={commentReactionTargetKind}
                  previewReactions={previewReactions}
                  onPreviewReactionChange={onPreviewReactionChange}
                  detailHref={detailHref}
                  detailLinkState={detailLinkState}
                  onMouseDown={stopNav}
                />
              )}
            </div>
          ) : (
            <PlayfulHint
              poolKey="comments_empty"
              fallback="Пока нет комментариев. Будьте первым."
              userId={viewerUserId}
              className="text-xs text-(--tgui--hint_color)"
            />
          )}

          <CommentComposeBar
            mode="singleLine"
            value={draft}
            onChange={onDraftChange}
            onSubmit={onSubmit}
            submitBusy={submitBusy}
            charsLeft={charsLeft}
            submitError={submitError}
            inputRef={draftInputRef}
            inlineMovieCardRefs={draftInlineCardRefs}
            onKeyDown={onDraftKeyDown}
            onInsertReaction={onInsertReaction}
            onToggleSpoiler={onToggleSpoiler}
            onInsertMovieCard={onInsertMovieCard}
            onMouseDown={stopNavKeepFocus}
          />
        </div>
      ) : null}
    </div>
  )
}
