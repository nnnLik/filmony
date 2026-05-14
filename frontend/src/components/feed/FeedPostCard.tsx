import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent, type MouseEventHandler } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, formatApiDetail, resolveApiUrl } from '../../api/client'
import type { WatchedInlinePickerItem } from '../../api/cardApi'
import type { FeedPostInFeed } from '../../api/feedInFeedTypes'
import {
  feedPostReferencedCardPoster,
  feedPostReferencedCardTitle,
  movieCardReleaseCompactSuffix,
} from '../../lib/movieCardDisplay'
import { createFeedPostComment, listAllFeedPostComments } from '../../api/feedPostApi'
import type { FeedPostComment, ReactionSummary, ReferencedMentionSnippet } from '../../api/profileTypes'
import { MentionProfileLookupProvider } from '../../context/MentionProfileLookupProvider'
import { displayNameFromAuthorFields } from '../../lib/authorDisplayName'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  movieCardRefTokenFromId,
  reactionTokenFromId,
} from '../../lib/commentReactionTokens'
import { inlineMovieCardRefMapFromSnippets, type InlineMovieCardRefMeta } from '../../lib/inlineMovieCardRefMap'
import { authorLikeToMentionRow } from '../../lib/mentionProfileLookupUtils'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { CommentDraftSingleLineInput } from '../comments/CommentDraftMirrorField'
import { MovieCardInlinePickerButton } from '../comments/MovieCardInlinePickerButton'
import { CommentReactionTokenPicker } from '../comments/CommentReactionTokenPicker'
import { ReactionStrip } from '../reactions/ReactionStrip'
import { formatCommentTime, formatRating } from './feedCardUtils'
import { feedPostSourceBadge } from './feedPostSourceBadge'
import { IconChevronDown, IconSend } from './FeedCardIcons'

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
}

function feedPostImageSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}

function authorName(comment: FeedPostComment): string {
  if (comment.author.display_name && comment.author.display_name.trim() !== '') {
    return comment.author.display_name
  }
  if (comment.author.username && comment.author.username.trim() !== '') {
    return `@${comment.author.username}`
  }
  const full = [comment.author.first_name, comment.author.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Пользователь' : full
}

function snippetPreview(text: string): string {
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= 72) return compact
  return `${compact.slice(0, 69)}...`
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
  } = post

  const referencedCardPoster =
    referenced_card != null ? feedPostReferencedCardPoster(referenced_card) : null
  const referencedCardTitle =
    referenced_card != null ? feedPostReferencedCardTitle(referenced_card) : ''
  const referencedReleaseSuffix =
    referenced_card != null ? movieCardReleaseCompactSuffix(referenced_card) : null
  const name = useMemo(() => displayNameFromAuthorFields(author), [author])
  const postHref = `/feed-posts/${id}`
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
  const [panelComments, setPanelComments] = useState<FeedPostComment[]>([])
  const [panelLoading, setPanelLoading] = useState(false)
  const [panelError, setPanelError] = useState<string | null>(null)
  if (post.id !== previewSync.postId || post.comments_preview !== previewSync.comments_preview) {
    setPreviewSync({ postId: post.id, comments_preview: post.comments_preview })
    setPreviewReactions({})
  }

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

  useEffect(() => {
    let cancelled = false
    if (!inlineComments || !commentsPreviewOpen || post.comments_count === 0) {
      void Promise.resolve().then(() => {
        if (cancelled) return
        setPanelComments([])
        setPanelLoading(false)
        setPanelError(null)
      })
      return () => {
        cancelled = true
      }
    }

    void Promise.resolve().then(() => {
      if (!cancelled) {
        setPanelLoading(true)
        setPanelError(null)
      }
    })

    void listAllFeedPostComments(post.id).then(
      (items) => {
        if (!cancelled) {
          setPanelComments(items)
          setPanelLoading(false)
        }
      },
      (e) => {
        if (!cancelled) {
          setPanelComments([])
          setPanelError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить комментарии')
          setPanelLoading(false)
        }
      },
    )

    return () => {
      cancelled = true
    }
  }, [commentsPreviewOpen, post.comments_count, post.id, inlineComments])

  const previewCommentsById = useMemo(() => {
    const map = new Map<number, FeedPostComment>()
    panelComments.forEach((c) => {
      map.set(c.id, c)
    })
    return map
  }, [panelComments])

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

  const sourceBadgeText = useMemo(
    () => feedPostSourceBadge(post, viewerUserId ?? null),
    [post, viewerUserId],
  )
  const isOwn =
    viewerUserId != null && viewerUserId !== '' && user_id === viewerUserId

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
    <div
      className="relative z-10 flex min-w-0 flex-col gap-1.5"
      onClick={linkToDetail ? stopPostNavClick : undefined}
    >
      <div className="flex min-w-0 items-center justify-between gap-2">
        <div
          className="min-w-0 flex-1 overflow-hidden py-px"
          onMouseDown={linkToDetail ? stopPostNav : undefined}
          onClick={linkToDetail ? stopPostNavClick : undefined}
        >
          <ReactionStrip
            targetKind="feed_post"
            targetId={id}
            summary={postReaction}
            onSummaryChange={setPostReaction}
            compact
          />
        </div>
        {inlineComments ? (
          <div
            className="flex shrink-0 items-center gap-1 border-l border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] pl-2"
            onMouseDown={linkToDetail ? stopPostNav : undefined}
            onClick={linkToDetail ? stopPostNavClick : undefined}
          >
            <span
              title="Комментарии"
              className="max-w-22 truncate text-[11px] font-medium leading-none text-(--tgui--hint_color) sm:max-w-none"
            >
              Комментарии
            </span>
            <span
              className="text-xs font-semibold tabular-nums leading-none text-(--tgui--text_color)"
              title="Всего комментариев к посту"
            >
              {post.comments_count}
            </span>
            <button
              type="button"
              onMouseDown={linkToDetail ? stopPostNav : undefined}
              onClick={(e) => {
                if (linkToDetail) stopPostNavClick(e)
                setCommentsPreviewOpen((open) => !open)
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

      {inlineComments && commentsPreviewOpen ? (
        <div
          className="flex flex-col gap-2 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_55%,transparent)] pt-2"
          onClick={linkToDetail ? stopPostNavClick : undefined}
        >
          {post.comments_count > 0 ? (
            <div
              className="max-h-[min(42vh,15rem)] min-h-30 overflow-y-auto overscroll-y-contain touch-pan-y space-y-1.5 pr-0.5 [-webkit-overflow-scrolling:touch]"
              role="region"
              aria-label="Комментарии к посту"
            >
              {panelLoading ? (
                <p className="py-6 text-center text-xs text-(--tgui--hint_color)">Загрузка…</p>
              ) : panelError != null ? (
                <p className="text-xs text-(--tgui--destructive_text_color,#ef4444)">
                  {panelError}{' '}
                  <Link to={postHref} state={{ fromFeed: true }} className="text-(--tgui--link_color) no-underline active:opacity-90">
                    Открыть пост
                  </Link>
                </p>
              ) : panelComments.length === 0 ? (
                <p className="text-xs text-(--tgui--hint_color)">
                  <Link to={postHref} state={{ fromFeed: true }} className="text-(--tgui--link_color) no-underline active:opacity-90">
                    Открыть пост
                  </Link>
                  , чтобы прочитать комментарии.
                </p>
              ) : (
                panelComments.map((comment) => {
                  const parentCommentId = comment.parent_comment_id
                  const parent =
                    parentCommentId != null ? previewCommentsById.get(parentCommentId) ?? null : null
                  const authorHref = `/u/${encodeURIComponent(comment.author.id)}`
                  return (
                    <div
                      key={comment.id}
                      className="rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2.5"
                    >
                      <div className="flex items-start gap-2">
                        <Link to={authorHref} className="shrink-0 no-underline" aria-label={`Профиль: ${authorName(comment)}`}>
                          <Avatar
                            src={comment.author.photo_url ?? undefined}
                            acronym={authorName(comment).slice(0, 2).toUpperCase()}
                            size={24}
                          />
                        </Link>
                        <div className="min-w-0 flex-1">
                          <div className="flex min-w-0 items-center justify-between gap-2">
                            <div className="flex min-w-0 flex-wrap items-center gap-2">
                              <span className="text-sm font-medium text-(--tgui--text_color)">{authorName(comment)}</span>
                              <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(comment.created_at)}</span>
                            </div>
                            <Link
                              to={postHref}
                              state={{ fromFeed: true }}
                              className="shrink-0 py-0 text-xs leading-none text-(--tgui--link_color) no-underline active:opacity-90"
                              onMouseDown={linkToDetail ? stopPostNav : undefined}
                            >
                              Ответить
                            </Link>
                          </div>

                          {parentCommentId != null ? (
                            <Link
                              to={postHref}
                              state={{ fromFeed: true }}
                              className="mt-2 block w-full rounded-lg border-l-2 border-(--tgui--link_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-left no-underline active:opacity-90"
                              onMouseDown={linkToDetail ? stopPostNav : undefined}
                            >
                              <p className="truncate text-xs font-medium text-(--tgui--link_color)">
                                {parent ? authorName(parent) : 'Родительский комментарий'}
                              </p>
                              <p className="truncate text-xs text-(--tgui--hint_color)">
                                {parent ? snippetPreview(parent.text) : 'Откройте пост, чтобы перейти к обсуждению'}
                              </p>
                            </Link>
                          ) : null}

                          <p className="mt-1 text-[13px] leading-snug text-(--tgui--text_color)">
                            <CommentBodyWithReactionTokens
                              text={comment.text}
                              className="whitespace-pre-wrap"
                              inlineMovieCardRefs={inlineMovieCardRefMapFromSnippets(comment.referenced_movie_cards)}
                              referencedMentions={comment.referenced_mentions}
                            />
                          </p>
                          <div className="mt-1.5 flex min-w-0 flex-nowrap items-center gap-x-1 overflow-hidden" onMouseDown={linkToDetail ? stopPostNav : undefined}>
                            <ReactionStrip
                              compact
                              targetKind="feed_post_comment"
                              targetId={comment.id}
                              summary={previewReactions[comment.id] ?? comment.reactions}
                              onSummaryChange={(next) =>
                                setPreviewReactions((prev) => ({ ...prev, [comment.id]: next }))
                              }
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          ) : (
            <p className="text-xs text-(--tgui--hint_color)">Пока нет комментариев. Будьте первым.</p>
          )}

          <div className="flex min-w-0 flex-col gap-1">
            <div
              className="relative z-10 flex min-w-0 items-stretch gap-1.5"
              onMouseDown={linkToDetail ? stopPostNavKeepFocus : undefined}
              onClick={linkToDetail ? stopPostNavClick : undefined}
            >
              <CommentDraftSingleLineInput
                ref={draftInputRef}
                value={draft}
                onChange={setDraft}
                disabled={submitBusy}
                maxLength={COMMENT_BODY_MAX_LEN}
                placeholder="Комментарий…"
                ariaLabel="Текст комментария"
                inlineMovieCardRefs={draftInlineCardRefs}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    void send()
                  }
                }}
              />
              <CommentReactionTokenPicker
                onPickReactionTypeId={insertReactionToken}
                disabled={submitBusy}
                allowInsert={draft.length < COMMENT_BODY_MAX_LEN}
              />
              <MovieCardInlinePickerButton
                onPick={insertMovieCardInline}
                disabled={submitBusy}
                allowInsert={draft.length < COMMENT_BODY_MAX_LEN}
              />
              <Button
                mode="filled"
                size="s"
                disabled={submitBusy || draft.trim().length === 0}
                type="button"
                className="min-h-8! min-w-8! shrink-0 px-0!"
                onClick={(e) => {
                  if (linkToDetail) stopPostNavClick(e)
                  void send()
                }}
                aria-label="Отправить комментарий"
              >
                {submitBusy ? '…' : <IconSend className="mx-auto size-4" />}
              </Button>
            </div>
            <div className="flex items-center justify-between gap-2 text-[10px] text-(--tgui--hint_color)">
              <span className="tabular-nums">{charsLeft}</span>
              {submitError != null ? (
                <span className="text-right text-(--tgui--destructive_text_color,#ef4444)">{submitError}</span>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
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
          <span
            className="shrink-0 rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_42%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-(--tgui--text_color)"
            title="Текстовый пост в ленте"
          >
            {sourceBadgeText}
          </span>
          {source_comment_id != null ? (
            <span
              className="shrink-0 rounded-md border border-(--tgui--divider_color) bg-(--tgui--section_bg_color) px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--hint_color)"
              title="Пост создан из вашего комментария к карточке"
            >
              Из комментария
            </span>
          ) : null}
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
                <span className="shrink-0 text-[11px] text-(--tgui--hint_color)">{formatCommentTime(created_at)}</span>
              </div>
            </div>
          </div>

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
                className="block truncate text-xs font-medium text-(--tgui--link_color) no-underline"
              >
                {displayNameFromAuthorFields(sourceCommentQuote.author)}
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

          {body.trim() !== '' ? (
            <FeedPostCardBody
              key={post.id}
              body={body}
              linkToDetail={linkToDetail}
              stopPostNav={stopPostNav}
              stopPostNavClick={stopPostNavClick}
              bodyInlineMovieCardRefs={bodyInlineRefMap}
              bodyReferencedMentions={body_referenced_mentions}
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
                  <img src={referencedCardPoster} alt="" className="h-full w-full object-cover" />
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
                  <span className="shrink-0 rounded-md bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] px-1.5 py-0.5 text-[12px] font-bold tabular-nums text-(--tgui--text_color)">
                    {formatRating(referenced_card.rating)}
                  </span>
                </div>
              </div>
            </Link>
          ) : null}

          {image_url != null && image_url.trim() !== '' ? (
            <div className="mt-1 overflow-hidden rounded-xl bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color)">
              <img
                src={feedPostImageSrc(image_url)}
                alt=""
                className="max-h-[min(70vw,18rem)] w-full object-cover object-center"
                loading="lazy"
              />
            </div>
          ) : null}
        </div>

        {engagementInner}
      </article>
    </MentionProfileLookupProvider>
  )
}
