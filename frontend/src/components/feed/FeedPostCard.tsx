import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent, type MouseEventHandler } from 'react'
import { Link, useNavigate } from 'react-router'

import { ApiError, formatApiDetail, resolveApiUrl } from '../../api/client'
import type { WatchedInlinePickerItem } from '../../api/cardApi'
import type { FeedPostInFeed } from '../../api/feedInFeedTypes'
import {
  feedPostReferencedCardPoster,
  feedPostReferencedCardTitle,
  movieCardReleaseCompactSuffix,
} from '../../lib/movieCardDisplay'
import {
  createFeedPostComment,
  deleteFeedPost,
  listAllFeedPostComments,
  updateFeedPost,
} from '../../api/feedPostApi'
import type { FeedPostComment, ReactionSummary, ReferencedMentionSnippet } from '../../api/profileTypes'
import { MentionProfileLookupProvider } from '../../context/MentionProfileLookupProvider'
import { displayNameFromAuthorFields } from '../../lib/authorDisplayName'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  movieCardRefTokenFromId,
  reactionTokenFromId,
} from '../../lib/commentReactionTokens'
import { toggleSpoilerAtSelection } from '../../lib/spoilerTokens'
import { inlineMovieCardRefMapFromSnippets, type InlineMovieCardRefMeta } from '../../lib/inlineMovieCardRefMap'
import { authorLikeToMentionRow } from '../../lib/mentionProfileLookupUtils'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import { useFeedCardAuthorBadges } from '../../hooks/useFeedCardAuthorBadges'
import { useFeedInlineCommentsPanel } from '../../hooks/useFeedInlineCommentsPanel'
import { useCommentScrollHighlight } from '../../hooks/useCommentScrollHighlight'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { WatchingNowAuthorBadge } from '../watchparty/WatchingNowAuthorBadge'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from '../comments/CommentDraftMirrorField'
import { EngagementCommentsRow } from './EngagementCommentsRow'
import { PlannedCardBadge } from '../cards/PlannedCardBadge'
import { CoViewSplitRatings } from './CoViewSplitRatings'
import { PostHeaderActions } from './PostHeaderActions'
import { formatCommentTime, formatRating } from './feedCardUtils'
import { FeedExplainabilityChip } from './FeedExplainabilityChip'
import {
  FeedOpenableContainedImage,
  FeedOpenableContainedImageThumbnail,
} from './FeedOpenableContainedImage'

export type FeedPostCardProps = {
  post: FeedPostInFeed
  viewerUserId?: string | null
  /** Если true (по умолчанию), клик по карточке открывает страницу поста */
  linkToDetail?: boolean
  /** Как карточка в ленте: раскрывающиеся комментарии и поле ввода. На странице поста выключите. */
  inlineComments?: boolean
  onCommentsState?: (
    postId: number,
    next: { comments_count: number; comments_preview: FeedPostComment[] },
  ) => void
  /** Called after the viewer successfully edits their own post body. */
  onPostUpdated?: (post: FeedPostInFeed) => void
  /** Called after the viewer successfully deletes their own post. */
  onPostDeleted?: (postId: number) => void
}

function feedPostImageSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}

type FeedPostCardBodyProps = {
  body: string
  linkToDetail: boolean
  stopPostNav: MouseEventHandler
  stopPostNavClick: MouseEventHandler
  bodyInlineMovieCardRefs?: ReadonlyMap<number, InlineMovieCardRefMeta>
  bodyReferencedMentions?: readonly ReferencedMentionSnippet[]
}

/** В ленте — line-clamp и «Ещё»; на странице поста — полный текст. */
function FeedPostCardBody({
  body,
  linkToDetail,
  stopPostNav,
  stopPostNavClick,
  bodyInlineMovieCardRefs,
  bodyReferencedMentions,
}: FeedPostCardBodyProps) {
  const clampRef = useRef<HTMLParagraphElement>(null)
  const [expanded, setExpanded] = useState(false)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    let alive = true
    if (!linkToDetail || expanded || body.trim() === '') {
      const id = requestAnimationFrame(() => {
        if (alive) setHasMore(false)
      })
      return () => {
        alive = false
        cancelAnimationFrame(id)
      }
    }
    const el = clampRef.current
    if (el == null) {
      const id = requestAnimationFrame(() => {
        if (alive) setHasMore(false)
      })
      return () => {
        alive = false
        cancelAnimationFrame(id)
      }
    }
    const measure = () => {
      if (!alive) return
      setHasMore(el.scrollHeight > el.clientHeight + 1)
    }
    const id0 = requestAnimationFrame(measure)
    const ro = new ResizeObserver(() => {
      requestAnimationFrame(measure)
    })
    ro.observe(el)
    return () => {
      alive = false
      cancelAnimationFrame(id0)
      ro.disconnect()
    }
  }, [linkToDetail, expanded, body])

  return (
    <div className="min-w-0">
      <p
        ref={linkToDetail ? clampRef : undefined}
        className={
          linkToDetail && !expanded
            ? 'line-clamp-6 min-w-0 wrap-break-word text-[13px] leading-relaxed text-(--tgui--text_color)'
            : 'min-w-0 wrap-break-word text-[13px] leading-relaxed text-(--tgui--text_color)'
        }
      >
        <CommentBodyWithReactionTokens
          text={body}
          className="text-[13px] leading-relaxed"
          inlineMovieCardRefs={bodyInlineMovieCardRefs}
          referencedMentions={bodyReferencedMentions}
        />
      </p>
      {linkToDetail && hasMore && !expanded ? (
        <Button
          type="button"
          size="s"
          mode="plain"
          className="-ms-1! mt-0.5! min-h-8! justify-start! px-1! text-xs! font-semibold"
          onMouseDown={stopPostNav}
          onClick={(e) => {
            stopPostNavClick(e)
            setExpanded(true)
          }}
        >
          Ещё
        </Button>
      ) : null}
      {linkToDetail && expanded ? (
        <Button
          type="button"
          size="s"
          mode="plain"
          className="-ms-1! mt-0.5! min-h-8! justify-start! px-1! text-xs! font-semibold"
          onMouseDown={stopPostNav}
          onClick={(e) => {
            stopPostNavClick(e)
            setExpanded(false)
          }}
        >
          Свернуть
        </Button>
      ) : null}
    </div>
  )
}

export function FeedPostCard({
  post,
  viewerUserId = null,
  linkToDetail = true,
  inlineComments = true,
  onCommentsState,
  onPostUpdated,
  onPostDeleted,
}: FeedPostCardProps) {
  const navigate = useNavigate()
  const {
    id,
    user_id,
    author,
    body,
    body_referenced_movie_cards,
    body_referenced_mentions,
    created_at,
    referenced_card,
    image_url,
    source_comment_id,
    source_comment: sourceCommentQuote,
    co_view_splits,
  } = post

  const referencedCardPoster =
    referenced_card != null ? feedPostReferencedCardPoster(referenced_card) : null
  const referencedCardTitle =
    referenced_card != null ? feedPostReferencedCardTitle(referenced_card) : ''
  const referencedReleaseSuffix =
    referenced_card != null ? movieCardReleaseCompactSuffix(referenced_card) : null
  const name = useMemo(() => displayNameFromAuthorFields(author), [author])
  const postHref = `/feed-posts/${id}`
  const navigateToPost = useCallback(() => {
    void navigate(postHref, { state: { fromFeed: true } })
  }, [navigate, postHref])
  const bodyInlineRefMap = useMemo(
    () => inlineMovieCardRefMapFromSnippets(body_referenced_movie_cards),
    [body_referenced_movie_cards],
  )
  const sourceQuoteInlineRefMap = useMemo(
    () => inlineMovieCardRefMapFromSnippets(sourceCommentQuote?.referenced_movie_cards),
    [sourceCommentQuote?.referenced_movie_cards],
  )
  const draftInputRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState('')
  const [draftInlineCardRefs, setDraftInlineCardRefs] = useState(
    () => new Map<number, { film_title: string; film_year: number | null }>(),
  )
  const [submitBusy, setSubmitBusy] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [commentsPreviewOpen, setCommentsPreviewOpen] = useState(false)
  const [reactionSync, setReactionSync] = useState(() => ({
    postId: post.id,
    reactions: post.reactions,
  }))
  const [postReaction, setPostReaction] = useState<ReactionSummary | undefined>(() => post.reactions)
  if (post.id !== reactionSync.postId || post.reactions !== reactionSync.reactions) {
    setReactionSync({ postId: post.id, reactions: post.reactions })
    setPostReaction(post.reactions)
  }

  const [previewSync, setPreviewSync] = useState(() => ({
    postId: post.id,
    comments_preview: post.comments_preview,
  }))
  const [previewReactions, setPreviewReactions] = useState<Record<number, ReactionSummary>>({})
  const [editingPost, setEditingPost] = useState(false)
  const [editBody, setEditBody] = useState('')
  const [editBusy, setEditBusy] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [bodyOverride, setBodyOverride] = useState<string | null>(null)
  const [editSync, setEditSync] = useState(() => ({ postId: post.id, body }))
  const displayBody = bodyOverride ?? body
  if (post.id !== editSync.postId || body !== editSync.body) {
    setEditSync({ postId: post.id, body })
    setBodyOverride(null)
    setEditingPost(false)
    setEditBody('')
    setEditError(null)
  }
  if (post.id !== previewSync.postId || post.comments_preview !== previewSync.comments_preview) {
    setPreviewSync({ postId: post.id, comments_preview: post.comments_preview })
    setPreviewReactions({})
  }

  const listAllComments = useCallback(
    (postId: number) => listAllFeedPostComments(postId),
    [],
  )
  const {
    panelComments,
    panelLoading,
    panelError,
    previewCommentsById,
  } = useFeedInlineCommentsPanel<FeedPostComment>({
    postId: post.id,
    commentsCount: post.comments_count,
    open: commentsPreviewOpen,
    enabled: inlineComments === true,
    listAllComments,
  })

  const { highlightCommentId, setCommentRef, scrollToComment } = useCommentScrollHighlight()

  const handleJumpToParent = useCallback(
    (parentCommentId: number) => {
      scrollToComment(parentCommentId)
    },
    [scrollToComment],
  )

  const handleInlineReply = useCallback(() => {
    draftInputRef.current?.focus()
  }, [])

  const mentionProfileRows = useMemo(() => {
    const rows = [authorLikeToMentionRow(author)]
    if (sourceCommentQuote != null) {
      rows.push(authorLikeToMentionRow(sourceCommentQuote.author))
    }
    for (const c of post.comments_preview) {
      rows.push(authorLikeToMentionRow(c.author))
    }
    for (const c of panelComments) {
      rows.push(authorLikeToMentionRow(c.author))
    }
    return rows
  }, [author, post.comments_preview, panelComments, sourceCommentQuote])

  const handleCancelPostEdit = useCallback(() => {
    setEditingPost(false)
    setEditBody('')
    setEditError(null)
  }, [])

  const handleStartPostEdit = useCallback(() => {
    setEditingPost(true)
    setEditBody(displayBody)
    setEditError(null)
    setDeleteError(null)
  }, [displayBody])

  const handleDeletePost = useCallback(async () => {
    if (deleteBusy) return
    const confirmed = window.confirm('Удалить пост? Комментарии тоже будут удалены.')
    if (!confirmed) return
    setDeleteBusy(true)
    setDeleteError(null)
    try {
      await deleteFeedPost(id)
      safeHapticSuccess()
      onPostDeleted?.(id)
    } catch (e) {
      setDeleteError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось удалить пост')
    } finally {
      setDeleteBusy(false)
    }
  }, [deleteBusy, id, onPostDeleted])

  const handleSavePostEdit = useCallback(async () => {
    if (editBusy) return
    const trimmed = editBody.trim()
    const hasImage = (image_url ?? '').trim() !== ''
    if (trimmed === '' && !hasImage) return
    setEditBusy(true)
    setEditError(null)
    try {
      const updated = await updateFeedPost(id, { body: editBody })
      setBodyOverride(updated.body)
      onPostUpdated?.(updated)
      setEditingPost(false)
      setEditBody('')
      safeHapticSuccess()
    } catch (e) {
      setEditError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось сохранить пост')
    } finally {
      setEditBusy(false)
    }
  }, [editBody, editBusy, id, image_url, onPostUpdated])

  const mergedPreviewAfterCreate = useCallback(
    (incoming: FeedPostComment) => {
      const nextCount = post.comments_count + 1
      const merged = [...post.comments_preview, incoming].sort((a, b) => a.id - b.id).slice(-3)
      onCommentsState?.(post.id, { comments_count: nextCount, comments_preview: merged })
      setCommentsPreviewOpen(true)
    },
    [onCommentsState, post.comments_count, post.comments_preview, post.id],
  )

  const send = useCallback(async () => {
    const text = draft.trim()
    if (text.length === 0) return
    setSubmitBusy(true)
    setSubmitError(null)
    try {
      const created = await createFeedPostComment(post.id, { text })
      mergedPreviewAfterCreate(created)
      setDraft('')
      setDraftInlineCardRefs(new Map())
      safeHapticSuccess()
    } catch (e) {
      setSubmitError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отправить')
    } finally {
      setSubmitBusy(false)
    }
  }, [draft, mergedPreviewAfterCreate, post.id])

  const insertReactionToken = useCallback(
    (reactionTypeId: number) => {
      const token = reactionTokenFromId(reactionTypeId)
      const el = draftInputRef.current
      const inserted = insertSnippetAtCaret(
        draft,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        COMMENT_BODY_MAX_LEN,
      )
      if (inserted == null) return
      setDraft(inserted.nextValue)
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [draft],
  )

  const insertMovieCardInline = useCallback(
    (row: WatchedInlinePickerItem) => {
      const token = movieCardRefTokenFromId(row.movie_card_id)
      const el = draftInputRef.current
      const inserted = insertSnippetAtCaret(
        draft,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        COMMENT_BODY_MAX_LEN,
      )
      if (inserted == null) return
      setDraft(inserted.nextValue)
      setDraftInlineCardRefs((prev) => {
        const next = new Map(prev)
        next.set(row.movie_card_id, { film_title: row.film_title, film_year: row.film_year })
        return next
      })
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [draft],
  )

  const toggleSpoilerInDraft = useCallback(() => {
    const el = draftInputRef.current
    const toggled = toggleSpoilerAtSelection(
      draft,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
      COMMENT_BODY_MAX_LEN,
    )
    if (toggled == null) return
    setDraft(toggled.nextValue)
    const caret = toggled.caret
    queueMicrotask(() => {
      el?.focus()
      el?.setSelectionRange(caret, caret)
    })
  }, [draft])

  const stopPostNav: MouseEventHandler = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const stopPostNavKeepFocus: MouseEventHandler = (e) => {
    e.stopPropagation()
  }

  /** Клик по реакциям/комментариям не должен открывать пост: у `article` есть onClick → navigate. */
  const stopPostNavClick: MouseEventHandler = (e) => {
    e.stopPropagation()
  }

  const isOwn =
    viewerUserId != null && viewerUserId !== '' && user_id === viewerUserId

  const panelCommentAuthorIds = useMemo(
    () => panelComments.map((comment) => comment.author.id),
    [panelComments],
  )
  const primaryTasteQuizOwnerIds = useMemo(() => {
    const ids: string[] = []
    if (!isOwn) {
      ids.push(user_id)
    }
    if (sourceCommentQuote != null) {
      ids.push(sourceCommentQuote.author.id)
    }
    return ids
  }, [isOwn, sourceCommentQuote, user_id])
  const primaryStreakUserIds = useMemo(() => {
    const ids = [user_id]
    if (sourceCommentQuote != null) {
      ids.push(sourceCommentQuote.author.id)
    }
    return ids
  }, [sourceCommentQuote, user_id])
  const { knowledgeByOwnerId, streakByUserId, watchingByUserId } = useFeedCardAuthorBadges({
    scopeKey: `feed_post:${id}`,
    tasteQuizOwnerIds: primaryTasteQuizOwnerIds,
    streakUserIds: primaryStreakUserIds,
    panelCommentAuthorIds,
  })

  const surfaceProps =
    linkToDetail === true
      ? {
          role: 'button' as const,
          tabIndex: 0,
          onClick: () => {
            void navigate(postHref, { state: { fromFeed: true } })
          },
          onKeyDown: (ev: KeyboardEvent) => {
            if (ev.key === 'Enter' || ev.key === ' ') {
              ev.preventDefault()
              void navigate(postHref, { state: { fromFeed: true } })
            }
          },
        }
      : {}

  const charsLeft = COMMENT_BODY_MAX_LEN - draft.length

  const engagementInner = (
    <EngagementCommentsRow
      commentsCount={post.comments_count}
      commentsPreviewOpen={commentsPreviewOpen}
      onTogglePreview={() => setCommentsPreviewOpen((open) => !open)}
      reactionTargetKind="feed_post"
      reactionTargetId={id}
      reactionSummary={postReaction}
      onReactionChange={setPostReaction}
      panelComments={panelComments}
      previewCommentsById={previewCommentsById}
      panelLoading={panelLoading}
      panelError={panelError}
      detailHref={postHref}
      detailLinkState={{ fromFeed: true }}
      viewerUserId={viewerUserId}
      knowledgeByAuthor={knowledgeByOwnerId}
      streakByUserId={streakByUserId}
      watchingByUserId={watchingByUserId}
      previewReactions={previewReactions}
      onPreviewReactionChange={(commentId, next) =>
        setPreviewReactions((prev) => ({ ...prev, [commentId]: next }))
      }
      commentReactionTargetKind="feed_post_comment"
      setCommentRef={setCommentRef}
      highlightCommentId={highlightCommentId}
      onJumpToParent={handleJumpToParent}
      onReply={handleInlineReply}
      draft={draft}
      onDraftChange={setDraft}
      draftInputRef={draftInputRef}
      draftInlineCardRefs={draftInlineCardRefs}
      onDraftKeyDown={(e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault()
          void send()
        }
      }}
      onInsertReaction={insertReactionToken}
      onToggleSpoiler={toggleSpoilerInDraft}
      onInsertMovieCard={insertMovieCardInline}
      onSubmit={() => void send()}
      submitBusy={submitBusy}
      submitError={submitError}
      charsLeft={charsLeft}
      stopNav={linkToDetail ? stopPostNav : undefined}
      stopNavKeepFocus={linkToDetail ? stopPostNavKeepFocus : undefined}
      stopNavClick={linkToDetail ? stopPostNavClick : undefined}
      linkToDetail={linkToDetail}
      detailFallbackLabel="Открыть пост"
      inlineCommentsEnabled={inlineComments === true}
    />
  )

  return (
    <MentionProfileLookupProvider value={mentionProfileRows}>
      <article
        data-testid={`feed-post-${id}`}
        data-feed-post-id={id}
        className={`feed-post-card flex max-w-full flex-col gap-2 overflow-hidden rounded-2xl p-2.5 shadow-[0_10px_40px_-14px_rgba(0,0,0,0.45)] ${
          linkToDetail ? 'cursor-pointer transition-opacity hover:opacity-[0.97]' : ''
        } ${
          isOwn
            ? 'border-2 border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_42%,transparent)] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
            : 'border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
        }`}
        {...surfaceProps}
      >
        <div className="mb-0.5 flex flex-wrap items-center gap-2 px-0.5">
          <FeedExplainabilityChip variant="post" post={post} viewerUserId={viewerUserId} />
          {source_comment_id != null ? (
            <span
              className="shrink-0 rounded-md border border-(--tgui--divider_color) bg-(--tgui--section_bg_color) px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--hint_color)"
              title="Пост создан из вашего комментария к карточке"
            >
              Из комментария
            </span>
          ) : null}
          {referenced_card?.is_planned ? <PlannedCardBadge variant="ribbon" /> : null}
        </div>

        <div className="flex min-w-0 flex-col gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <Link
              to={`/u/${encodeURIComponent(user_id)}`}
              onClick={(e) => {
                if (linkToDetail) e.stopPropagation()
              }}
              className="relative z-10 flex shrink-0 rounded-full p-0.5 no-underline ring-1 ring-transparent transition-[box-shadow,ring-color] hover:ring-(--tgui--link_color) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--tgui--link_color)"
              title={name}
              aria-label={`Профиль: ${name}`}
            >
              <Avatar
                size={22}
                src={author.photo_url ?? undefined}
                acronym={(name.slice(0, 1) || '?').toUpperCase()}
              />
            </Link>
            <div className="min-w-0 flex-1">
              <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <Link
                  to={`/u/${encodeURIComponent(user_id)}`}
                  onClick={(e) => {
                    if (linkToDetail) e.stopPropagation()
                  }}
                  className="truncate text-sm font-medium text-(--tgui--link_color) no-underline"
                >
                  {name}
                </Link>
                <TasteQuizCommentAuthorBadge
                  knowledgeByAuthor={knowledgeByOwnerId}
                  authorId={user_id}
                  viewerId={viewerUserId}
                />
                <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={user_id} />
                <WatchingNowAuthorBadge watchingByUserId={watchingByUserId} authorId={user_id} />
                <span className="shrink-0 text-[11px] text-(--tgui--hint_color)">{formatCommentTime(created_at)}</span>
              </div>
            </div>
            {isOwn && !editingPost ? (
              <div
                onMouseDown={linkToDetail ? stopPostNav : undefined}
                onClick={linkToDetail ? stopPostNavClick : undefined}
              >
                <PostHeaderActions
                  canManage={isOwn}
                  onEdit={handleStartPostEdit}
                  onDelete={() => void handleDeletePost()}
                  busy={editBusy}
                  deleteBusy={deleteBusy}
                  disabled={editBusy}
                />
              </div>
            ) : null}
          </div>

          {deleteError != null ? (
            <p className="text-xs text-(--tgui--destructive_text_color)">{deleteError}</p>
          ) : null}

          {sourceCommentQuote != null ? (
            <div
              onClick={stopPostNavClick}
              className="rounded-lg border-l-2 border-(--tgui--link_color) bg-(--tgui--secondary_bg_color) px-2 py-1.5"
            >
              <Link
                to={`/u/${encodeURIComponent(sourceCommentQuote.author.id)}`}
                onClick={(e) => {
                  if (linkToDetail) e.stopPropagation()
                }}
                className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5 truncate text-xs font-medium text-(--tgui--link_color) no-underline"
              >
                {displayNameFromAuthorFields(sourceCommentQuote.author)}
                <TasteQuizCommentAuthorBadge
                  knowledgeByAuthor={knowledgeByOwnerId}
                  authorId={sourceCommentQuote.author.id}
                  viewerId={viewerUserId}
                />
                <RatingStreakAuthorBadge
                  streakByUserId={streakByUserId}
                  authorId={sourceCommentQuote.author.id}
                />
                <WatchingNowAuthorBadge
                  watchingByUserId={watchingByUserId}
                  authorId={sourceCommentQuote.author.id}
                />
              </Link>
              {sourceCommentQuote.text.trim() !== '' ? (
                <p className="mt-1 text-xs leading-relaxed text-(--tgui--hint_color)">
                  <CommentBodyWithReactionTokens
                    text={sourceCommentQuote.text}
                    className="whitespace-pre-wrap"
                    inlineMovieCardRefs={sourceQuoteInlineRefMap}
                    referencedMentions={sourceCommentQuote.referenced_mentions}
                  />
                </p>
              ) : sourceCommentQuote.image_url != null && String(sourceCommentQuote.image_url).trim() !== '' ? (
                <p className="mt-1 text-[11px] leading-snug text-(--tgui--hint_color)">
                  В комментарии было только изображение — оно перенесено в пост ниже.
                </p>
              ) : null}
            </div>
          ) : null}

          {editingPost ? (
            <div
              className="space-y-2"
              onMouseDown={linkToDetail ? stopPostNav : undefined}
              onClick={linkToDetail ? stopPostNavClick : undefined}
            >
              <CommentDraftMultiline
                value={editBody}
                onChange={setEditBody}
                disabled={editBusy}
                rows={4}
                placeholder="Редактировать пост"
                inlineMovieCardRefs={bodyInlineRefMap}
              />
              {editError != null ? (
                <p className="text-xs text-(--tgui--destructive_text_color)">{editError}</p>
              ) : null}
              <div className="flex gap-2">
                <Button
                  size="s"
                  disabled={
                    editBusy || (editBody.trim() === '' && (image_url ?? '').trim() === '')
                  }
                  onClick={() => void handleSavePostEdit()}
                >
                  {editBusy ? 'Сохранение…' : 'Сохранить'}
                </Button>
                <Button size="s" mode="gray" disabled={editBusy} onClick={handleCancelPostEdit}>
                  Отмена
                </Button>
              </div>
            </div>
          ) : displayBody.trim() !== '' ? (
            <FeedPostCardBody
              key={post.id}
              body={displayBody}
              linkToDetail={linkToDetail}
              stopPostNav={stopPostNav}
              stopPostNavClick={stopPostNavClick}
              bodyInlineMovieCardRefs={bodyInlineRefMap}
              bodyReferencedMentions={body_referenced_mentions}
            />
          ) : null}

          {co_view_splits != null && co_view_splits.length > 0 ? (
            <CoViewSplitRatings
              splits={co_view_splits}
              onLinkClick={linkToDetail ? stopPostNavClick : undefined}
            />
          ) : null}

          {referenced_card != null ? (
            <Link
              to={`/cards/${referenced_card.movie_card_id}`}
              state={{ fromFeed: true }}
              onClick={(e) => {
                if (linkToDetail) e.stopPropagation()
              }}
              className="flex min-w-0 gap-2.5 rounded-xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] p-2 no-underline transition-[border-color,box-shadow] active:opacity-95 hover:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_28%,var(--tgui--divider_color))]"
            >
              <div className="relative h-14 w-10 shrink-0 overflow-hidden rounded-lg bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color)">
                {referencedCardPoster ? (
                  <FeedOpenableContainedImageThumbnail
                    src={referencedCardPoster}
                    wrapperClassName="relative block h-full w-full"
                    imgClassName="absolute inset-0 size-full object-cover object-top bg-(--tgui--divider_color)"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-[9px] text-(--tgui--hint_color)">
                    н/д
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1 py-0.5">
                <div className="flex min-w-0 items-start justify-between gap-2">
                  <p className="line-clamp-2 min-w-0 flex-1 text-[13px] font-semibold leading-snug text-(--tgui--text_color)">
                    {referencedCardTitle}
                    {referencedReleaseSuffix != null ? (
                      <span className="font-normal text-(--tgui--hint_color)">
                        {' '}
                        · {referencedReleaseSuffix}
                      </span>
                    ) : null}
                  </p>
                  {referenced_card.is_planned ? (
                    <PlannedCardBadge variant="inline" />
                  ) : (
                    <span className="shrink-0 rounded-md bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] px-1.5 py-0.5 text-[12px] font-bold tabular-nums text-(--tgui--text_color)">
                      {formatRating(referenced_card.rating)}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ) : null}

          {image_url != null && image_url.trim() !== '' ? (
            <FeedOpenableContainedImage
              src={feedPostImageSrc(image_url)}
              ariaLabel={`Открыть пост из ленты`}
              wrapperClassName="relative mt-1 block w-full overflow-hidden rounded-xl bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color)"
              imgClassName="pointer-events-none block h-auto w-full max-w-none bg-(--tgui--divider_color)"
              loading="lazy"
              onSingleNavigate={linkToDetail ? navigateToPost : null}
            />
          ) : null}
        </div>

        {engagementInner}
      </article>
    </MentionProfileLookupProvider>
  )
}
