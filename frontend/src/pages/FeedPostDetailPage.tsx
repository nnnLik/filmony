import { Avatar, Button, IconButton } from '@telegram-apps/telegram-ui'
import { ArrowLeft } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEventHandler,
} from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import {
  createFeedPostComment,
  getFeedPostById,
  getFeedPostComments,
} from '../api/feedPostApi'
import { getMyProfile, getUserSubscriptions } from '../api/profileApi'
import { ApiError, formatApiDetail } from '../api/client'
import type { FeedPostInFeed } from '../api/feedInFeedTypes'
import type { FeedPostComment, ReactionSummary } from '../api/profileTypes'
import { CommentBodyWithReactionTokens } from '../components/comments/CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from '../components/comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../components/comments/CommentReactionTokenPicker'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import { ReactionStrip } from '../components/reactions/ReactionStrip'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { COMMENT_BODY_MAX_LEN, insertSnippetAtCaret, reactionTokenFromId } from '../lib/commentReactionTokens'
import {
  applyMentionPick,
  mentionReplacementFromSlug,
  parseActiveMentionQuery,
  type ActiveMentionQuery,
} from '../lib/feedMentionCompose'
import { filterFollowingForMentionQuery } from '../lib/mentionFollowingFilter'
import { markGlobalFeedPostDetailOpened } from '../lib/globalFeedViewedIds'
import {
  authorLikeToMentionRow,
  mentionProfileKeyFromSlug,
  subscriptionToMentionRow,
  type MentionProfileRowInput,
} from '../lib/mentionProfileLookupUtils'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { displayNameFromProfile } from '../lib/profileDisplay'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { useMentionPopoverLayout } from '../lib/useMentionPopoverLayout'

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

function snippet(text: string): string {
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= 72) return compact
  return `${compact.slice(0, 69)}...`
}

function formatCommentTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function FeedPostDetailPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams<{ postId: string }>()
  const parsedPostId = useMemo(() => {
    const n = Number(params.postId)
    return Number.isInteger(n) && n >= 1 ? n : null
  }, [params.postId])

  const [post, setPost] = useState<FeedPostInFeed | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)
  const [comments, setComments] = useState<FeedPostComment[]>([])
  const [commentsNextCursor, setCommentsNextCursor] = useState<string | null>(null)
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)
  const [jumpBusy, setJumpBusy] = useState(false)
  const [highlightCommentId, setHighlightCommentId] = useState<number | null>(null)
  const commentRefs = useRef<Record<number, HTMLDivElement | null>>({})
  const commentTextAreaRef = useRef<HTMLTextAreaElement>(null)

  const commentsById = useMemo(() => {
    const map = new Map<number, FeedPostComment>()
    comments.forEach((c) => map.set(c.id, c))
    return map
  }, [comments])

  const followingForMentionsQuery = useQuery({
    queryKey: ['userSubscriptions', viewerId, 'following'],
    queryFn: () => getUserSubscriptions(viewerId as string, 'following'),
    enabled: viewerId != null,
    staleTime: 60_000,
  })
  const followingMentionItems = useMemo(
    () => followingForMentionsQuery.data?.items ?? [],
    [followingForMentionsQuery.data],
  )

  const mentionRowsForPostDetail = useMemo((): MentionProfileRowInput[] => {
    const seen = new Set<string>()
    const out: MentionProfileRowInput[] = []
    const push = (r: MentionProfileRowInput) => {
      const k = mentionProfileKeyFromSlug(r.profile_slug)
      if (k.length === 0 || seen.has(k)) return
      seen.add(k)
      out.push(r)
    }
    if (post != null) push(authorLikeToMentionRow(post.author))
    for (const c of comments) push(authorLikeToMentionRow(c.author))
    for (const it of followingMentionItems) push(subscriptionToMentionRow(it))
    return out
  }, [comments, followingMentionItems, post])

  const [commentMentionPicker, setCommentMentionPicker] = useState<ActiveMentionQuery | null>(null)
  const [commentMentionHighlightIdx, setCommentMentionHighlightIdx] = useState(0)
  const commentMentionAnchorRef = useRef<HTMLDivElement>(null)

  const commentMentionFiltered = useMemo(
    () =>
      commentMentionPicker != null
        ? filterFollowingForMentionQuery(followingMentionItems, commentMentionPicker.query)
        : [],
    [commentMentionPicker, followingMentionItems],
  )

  const commentMentionHighlightSafe = useMemo(() => {
    if (commentMentionFiltered.length === 0) return 0
    return Math.min(commentMentionHighlightIdx, commentMentionFiltered.length - 1)
  }, [commentMentionFiltered.length, commentMentionHighlightIdx])

  const commentMentionPopoverLayout = useMentionPopoverLayout(commentMentionPicker != null, commentMentionAnchorRef)

  const syncCommentMentionFromValue = useCallback((value: string, caretOverride?: number | null) => {
    const el = commentTextAreaRef.current
    const caret =
      caretOverride != null
        ? Math.min(Math.max(0, caretOverride), value.length)
        : Math.min(el?.selectionStart ?? value.length, value.length)
    const active = parseActiveMentionQuery(value, caret)
    if (active == null) {
      setCommentMentionPicker(null)
      setCommentMentionHighlightIdx(0)
      return
    }
    setCommentMentionPicker(active)
    setCommentMentionHighlightIdx(0)
  }, [])

  const handleCommentTextChange = useCallback(
    (v: string, meta?: { caret: number }) => {
      const next = v.slice(0, COMMENT_BODY_MAX_LEN)
      setCommentText(next)
      const caret = meta?.caret ?? next.length
      queueMicrotask(() => syncCommentMentionFromValue(next, caret))
    },
    [syncCommentMentionFromValue],
  )

  const pickCommentMention = useCallback(
    (slug: string) => {
      const el = commentTextAreaRef.current
      if (commentMentionPicker == null || el == null) return
      const endCaret = commentMentionPicker.atIndex + 1 + commentMentionPicker.query.length
      const caret = Math.min(endCaret, commentText.length)
      const token = mentionReplacementFromSlug(slug)
      const res = applyMentionPick(commentText, caret, commentMentionPicker.atIndex, token, COMMENT_BODY_MAX_LEN)
      if (res == null) return
      setCommentText(res.nextValue)
      setCommentMentionPicker(null)
      setCommentMentionHighlightIdx(0)
      queueMicrotask(() => {
        el.focus()
        el.setSelectionRange(res.caret, res.caret)
      })
    },
    [commentMentionPicker, commentText],
  )

  const handleCommentDraftKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = useCallback(
    (e) => {
      if (commentMentionPicker == null) return
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setCommentMentionHighlightIdx((i) => {
          const max = Math.max(0, commentMentionFiltered.length - 1)
          return Math.min(max, i + 1)
        })
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setCommentMentionHighlightIdx((i) => Math.max(0, i - 1))
      } else if (e.key === 'Enter' && commentMentionFiltered.length > 0) {
        e.preventDefault()
        const row = commentMentionFiltered[commentMentionHighlightSafe] ?? commentMentionFiltered[0]
        if (row != null) {
          pickCommentMention(row.profile_slug)
        }
      }
    },
    [commentMentionFiltered, commentMentionHighlightSafe, commentMentionPicker, pickCommentMention],
  )

  useEffect(() => {
    if (viewerId != null) return
    let alive = true
    void (async () => {
      try {
        const profile = await getMyProfile()
        if (!alive) return
        setViewerId(profile.id)
      } catch {
        void 0
      }
    })()
    return () => {
      alive = false
    }
  }, [viewerId])

  useEffect(() => {
    if (parsedPostId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = await getFeedPostById(parsedPostId)
        if (!alive) return
        setPost(item)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) setError(formatApiDetail(e.detail))
        else setError('Не удалось загрузить пост')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedPostId])

  useEffect(() => {
    if (parsedPostId == null || post == null) return
    markGlobalFeedPostDetailOpened(parsedPostId)
  }, [parsedPostId, post])

  const loadComments = useCallback(
    async (append: boolean) => {
      if (parsedPostId == null) return
      const cursor = append ? commentsNextCursor : null
      if (append && cursor == null) return
      setCommentsLoading(true)
      if (!append) setCommentsError(null)
      try {
        const page = await getFeedPostComments(parsedPostId, { cursor, limit: 20 })
        setComments((prev) => (append ? [...prev, ...page.items] : page.items))
        setCommentsNextCursor(page.next_cursor ?? null)
      } catch (e) {
        if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
        else setCommentsError('Не удалось загрузить комментарии')
      } finally {
        setCommentsLoading(false)
      }
    },
    [commentsNextCursor, parsedPostId],
  )

  useEffect(() => {
    if (parsedPostId == null || error != null || post == null) return
    let alive = true
    void (async () => {
      if (!alive) return
      await loadComments(false)
    })()
    return () => {
      alive = false
    }
  }, [parsedPostId, error, post, loadComments])

  const scrollToComment = useCallback((commentId: number): boolean => {
    const target = commentRefs.current[commentId]
    if (target == null) return false
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setHighlightCommentId(commentId)
    window.setTimeout(() => {
      setHighlightCommentId((prev) => (prev === commentId ? null : prev))
    }, 1700)
    return true
  }, [])

  const insertReactionIntoComment = useCallback(
    (reactionTypeId: number) => {
      setCommentMentionPicker(null)
      setCommentMentionHighlightIdx(0)
      const token = reactionTokenFromId(reactionTypeId)
      const el = commentTextAreaRef.current
      const inserted = insertSnippetAtCaret(
        commentText,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        COMMENT_BODY_MAX_LEN,
      )
      if (inserted == null) return
      setCommentText(inserted.nextValue)
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [commentText],
  )

  async function handleCreateComment() {
    if (parsedPostId == null || submitBusy) return
    const text = commentText.trim()
    if (text === '') return
    setSubmitBusy(true)
    setCommentsError(null)
    try {
      await createFeedPostComment(parsedPostId, {
        text,
        parent_comment_id: replyTo?.id ?? null,
      })
      await loadComments(false)
      try {
        const fresh = await getFeedPostById(parsedPostId)
        setPost(fresh)
      } catch {
        void 0
      }
      setCommentText('')
      setCommentMentionPicker(null)
      setCommentMentionHighlightIdx(0)
      setReplyTo(null)
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
      else setCommentsError('Не удалось отправить комментарий')
    } finally {
      setSubmitBusy(false)
    }
  }

  async function handleJumpToParent(parentCommentId: number) {
    if (parsedPostId == null || jumpBusy) return
    setCommentsError(null)
    if (commentsById.has(parentCommentId)) {
      scrollToComment(parentCommentId)
      return
    }
    setJumpBusy(true)
    try {
      let cursor = commentsNextCursor
      let accumulated = comments
      while (cursor != null && !accumulated.some((item) => item.id === parentCommentId)) {
        const page = await getFeedPostComments(parsedPostId, { cursor, limit: 20 })
        accumulated = [...accumulated, ...page.items]
        cursor = page.next_cursor ?? null
      }
      setComments(accumulated)
      setCommentsNextCursor(cursor)
      if (!accumulated.some((item) => item.id === parentCommentId)) {
        setCommentsError('Родительский комментарий не найден')
        return
      }
      window.requestAnimationFrame(() => scrollToComment(parentCommentId))
    } catch (e) {
      if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
      else setCommentsError('Не удалось загрузить родительский комментарий')
    } finally {
      setJumpBusy(false)
    }
  }

  const charsLeft = COMMENT_BODY_MAX_LEN - commentText.length
  const invalidPostId = parsedPostId == null
  const showLoading = !invalidPostId && loading

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_92%,transparent)] px-3 py-2 backdrop-blur-md">
        <IconButton
          size="s"
          mode="gray"
          aria-label="Назад"
          onClick={() => {
            const st = location.state as { fromFeed?: boolean } | undefined
            if (st?.fromFeed) void navigate('/')
            else void navigate(-1)
          }}
        >
          <ArrowLeft className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
        </IconButton>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Пост</span>
      </header>

      <main className="mx-auto max-w-md px-3 pb-10 pt-3 sm:px-4">
        {invalidPostId ? (
          <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">
            Некорректный адрес поста
          </p>
        ) : null}

        {showLoading ? (
          <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {error != null ? (
          <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
        ) : null}

        {!showLoading && post != null ? (
          <MentionProfileLookupProvider value={mentionRowsForPostDetail}>
            <FeedPostCard post={post} viewerUserId={viewerId} linkToDetail={false} inlineComments={false} />

            <section className="mt-4 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 sm:p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">
                Комментарии
              </p>

              {replyTo != null ? (
                <div className="mt-2 flex items-center justify-between rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,var(--tgui--divider_color))] bg-(--tgui--bg_color) px-3 py-2 text-xs">
                  <span className="text-(--tgui--hint_color)">Ответ для: {replyTo.label}</span>
                  <button type="button" onClick={() => setReplyTo(null)} className="text-(--tgui--link_color)">
                    отменить
                  </button>
                </div>
              ) : null}

              <div className="mt-3">
                <div className="flex gap-2">
                  <div ref={commentMentionAnchorRef} className="relative min-w-0 flex-1">
                    <CommentDraftMultiline
                      ref={commentTextAreaRef}
                      value={commentText}
                      onChange={handleCommentTextChange}
                      onKeyDown={handleCommentDraftKeyDown}
                      onKeyUp={() => {
                        const el = commentTextAreaRef.current
                        if (el == null) return
                        syncCommentMentionFromValue(
                          el.value.slice(0, COMMENT_BODY_MAX_LEN),
                          el.selectionStart ?? el.value.length,
                        )
                      }}
                      onSelect={() => {
                        const el = commentTextAreaRef.current
                        if (el == null) return
                        syncCommentMentionFromValue(
                          el.value.slice(0, COMMENT_BODY_MAX_LEN),
                          el.selectionStart ?? el.value.length,
                        )
                      }}
                      disabled={submitBusy}
                      rows={4}
                      maxLength={COMMENT_BODY_MAX_LEN}
                      placeholder="Напишите комментарий..."
                    />
                    {commentMentionPicker != null && commentMentionPopoverLayout != null
                      ? createPortal(
                          <>
                            <button
                              type="button"
                              tabIndex={-1}
                              aria-hidden
                              className="fixed inset-0 z-[200] cursor-default bg-black/0"
                              onClick={() => {
                                setCommentMentionPicker(null)
                                setCommentMentionHighlightIdx(0)
                              }}
                            />
                            <div
                              className="filmony-theme fixed z-[201] overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) py-1 shadow-lg"
                              style={{
                                top: commentMentionPopoverLayout.top,
                                left: commentMentionPopoverLayout.left,
                                width: commentMentionPopoverLayout.width,
                                maxHeight: commentMentionPopoverLayout.maxHeight,
                              }}
                              role="listbox"
                              aria-label="Упомянуть подписку"
                            >
                              {followingForMentionsQuery.isPending ? (
                                <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
                              ) : followingForMentionsQuery.isError ? (
                                <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">
                                  Не удалось загрузить подписки
                                </p>
                              ) : followingMentionItems.length === 0 ? (
                                <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">
                                  Подпишитесь на пользователей — здесь появятся упоминания.
                                </p>
                              ) : commentMentionFiltered.length === 0 ? (
                                <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Нет совпадений</p>
                              ) : (
                                commentMentionFiltered.map((it, idx) => {
                                  const label = displayNameFromProfile(it)
                                  const selected = idx === commentMentionHighlightSafe
                                  return (
                                    <button
                                      key={it.id}
                                      type="button"
                                      role="option"
                                      aria-selected={selected}
                                      className={`flex w-full flex-col gap-0.5 px-3 py-2 text-left transition active:opacity-90 ${
                                        selected
                                          ? 'bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,var(--tgui--secondary_bg_color))]'
                                          : 'hover:bg-(--tgui--secondary_bg_color)'
                                      }`}
                                      onMouseDown={(ev) => {
                                        ev.preventDefault()
                                        pickCommentMention(it.profile_slug)
                                      }}
                                    >
                                      <span className="text-[13px] font-medium text-(--tgui--text_color)">{label}</span>
                                      <span className="font-mono text-[11px] text-(--tgui--hint_color)">
                                        @{it.profile_slug}
                                      </span>
                                    </button>
                                  )
                                })
                              )}
                            </div>
                          </>,
                          document.body,
                        )
                      : null}
                  </div>
                  <div className="flex shrink-0 flex-col justify-start pt-1">
                    <CommentReactionTokenPicker
                      onPickReactionTypeId={insertReactionIntoComment}
                      disabled={submitBusy}
                      allowInsert={commentText.length < COMMENT_BODY_MAX_LEN}
                    />
                  </div>
                </div>
                <div className="mt-1 flex items-center justify-between gap-2">
                  <span
                    className={`text-xs ${charsLeft < 20 ? 'text-(--tgui--destructive_text_color)' : 'text-(--tgui--hint_color)'}`}
                  >
                    Осталось: {charsLeft}
                  </span>
                  <Button
                    size="s"
                    disabled={submitBusy || commentText.trim() === ''}
                    onClick={() => void handleCreateComment()}
                  >
                    {submitBusy ? 'Отправка...' : 'Отправить'}
                  </Button>
                </div>
              </div>

              {commentsError != null ? (
                <p className="mt-2 text-sm text-(--tgui--destructive_text_color)">{commentsError}</p>
              ) : null}

              {commentsLoading ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Загрузка комментариев…</p>
              ) : null}

              {!commentsLoading && comments.length === 0 ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока нет комментариев.</p>
              ) : null}

              {comments.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {comments.map((comment) => {
                    const parent =
                      comment.parent_comment_id != null
                        ? commentsById.get(comment.parent_comment_id) ?? null
                        : null
                    const parentCommentId = comment.parent_comment_id
                    return (
                      <div
                        key={comment.id}
                        ref={(element) => {
                          commentRefs.current[comment.id] = element
                        }}
                        className={`rounded-xl border bg-(--tgui--bg_color) p-3 ${
                          highlightCommentId === comment.id
                            ? 'border-(--tgui--link_color) shadow-[0_0_0_2px_color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)]'
                            : 'border-(--tgui--divider_color)'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <Link
                            to={`/u/${encodeURIComponent(comment.author.id)}`}
                            className="no-underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Avatar
                              src={comment.author.photo_url ?? undefined}
                              acronym={authorName(comment).slice(0, 2).toUpperCase()}
                              size={28}
                            />
                          </Link>
                          <div className="min-w-0 flex-1">
                            <div className="flex min-w-0 items-center justify-between gap-2">
                              <div className="flex min-w-0 flex-wrap items-center gap-2">
                                <Link
                                  to={`/u/${encodeURIComponent(comment.author.id)}`}
                                  className="text-sm font-medium text-(--tgui--link_color) no-underline"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {authorName(comment)}
                                </Link>
                                <span className="text-xs text-(--tgui--hint_color)">
                                  {formatCommentTime(comment.created_at)}
                                </span>
                              </div>
                              <button
                                type="button"
                                onClick={() => setReplyTo({ id: comment.id, label: authorName(comment) })}
                                className="inline-flex bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--link_color)"
                              >
                                Ответить
                              </button>
                            </div>

                            {parentCommentId != null ? (
                              <button
                                type="button"
                                onClick={() => void handleJumpToParent(parentCommentId)}
                                className="mt-2 block w-full rounded-lg border-l-2 border-(--tgui--link_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-left"
                                disabled={jumpBusy}
                              >
                                <p className="truncate text-xs font-medium text-(--tgui--link_color)">
                                  {parent ? authorName(parent) : 'Родительский комментарий'}
                                </p>
                                <p className="truncate text-xs text-(--tgui--hint_color)">
                                  {parent ? snippet(parent.text) : 'Нажмите, чтобы подгрузить и перейти'}
                                </p>
                              </button>
                            ) : null}

                            <p className="mt-1 text-sm leading-relaxed">
                              <CommentBodyWithReactionTokens text={comment.text} className="whitespace-pre-wrap" />
                            </p>
                            <div className="mt-1.5 flex min-w-0 flex-nowrap items-center gap-x-1 overflow-hidden">
                              <ReactionStrip
                                compact
                                targetKind="feed_post_comment"
                                targetId={comment.id}
                                summary={comment.reactions}
                                onSummaryChange={(next: ReactionSummary) =>
                                  setComments((prev) =>
                                    prev.map((c) => (c.id === comment.id ? { ...c, reactions: next } : c)),
                                  )
                                }
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
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
          </MentionProfileLookupProvider>
        ) : null}
      </main>
    </div>
  )
}
