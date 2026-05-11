import { Avatar, Button, IconButton, Title } from '@telegram-apps/telegram-ui'
import { CopyPlus, Link2, Share2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type Dispatch,
  type KeyboardEventHandler,
  type MutableRefObject,
  type RefObject,
  type SetStateAction,
} from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { createPortal } from 'react-dom'

import { createMovieCardComment, getFollowingRatingsForCard, getMovieCardById, getMovieCardComments } from '../api/cardApi'
import { getUserSubscriptions } from '../api/profileApi'
import type { SubscriptionListItem } from '../api/profileTypes'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile } from '../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MovieCard,
  MovieCardComment,
  MovieCardCommentAuthor,
  ReactionSummary,
} from '../api/profileTypes'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'
import { copyTextToClipboard } from '../lib/copyTextToClipboard'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { COMMENT_BODY_MAX_LEN, insertSnippetAtCaret, reactionTokenFromId } from '../lib/commentReactionTokens'
import {
  authorLikeToMentionRow,
  mentionProfileKeyFromSlug,
  subscriptionToMentionRow,
  type MentionProfileRowInput,
} from '../lib/mentionProfileLookupUtils'
import {
  applyMentionPick,
  mentionReplacementFromSlug,
  parseActiveMentionQuery,
  type ActiveMentionQuery,
} from '../lib/feedMentionCompose'
import { useMentionPopoverLayout } from '../lib/useMentionPopoverLayout'
import { buildMiniAppCardDeepLink } from '../lib/miniAppCardDeepLink'
import { kinopoiskTitleUrl, openExternalUrl } from '../lib/openExternalUrl'
import { markGlobalFeedCardDetailOpened } from '../lib/globalFeedViewedIds'
import { recordRecentCardView } from '../lib/recentCardViews'
import { CommentBodyWithReactionTokens } from '../components/comments/CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from '../components/comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../components/comments/CommentReactionTokenPicker'
import { ReactionStrip } from '../components/reactions/ReactionStrip'
import { FavoriteCardHeartButton } from '../components/cards/FavoriteCardHeartButton'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { FilmSynopsisBlock } from '../components/films/FilmSynopsisBlock'
import { useRemoveMovieCard } from '../hooks/useRemoveMovieCard'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { useComposeFeedPost } from '../compose/useComposeFeedPost'

function filterFollowingForMentionQuery(
  items: SubscriptionListItem[],
  query: string,
): SubscriptionListItem[] {
  const n = query.trim().toLowerCase()
  if (n === '') {
    return items
  }
  return items.filter((it) => {
    const slug = it.profile_slug.toLowerCase()
    const dn = (it.display_name ?? '').toLowerCase()
    const un = (it.username ?? '').toLowerCase()
    return slug.startsWith(n) || dn.includes(n) || un.includes(n)
  })
}

const COMPANY_LABELS: Record<CardCompany, string> = {
  alone: 'Один',
  partner: 'С партнером',
  friends: 'С друзьями',
  family: 'С семьей',
}

const MOOD_BEFORE_LABELS: Record<CardMoodBefore, string> = {
  relax: 'Расслабиться',
  laugh: 'Поржать',
  sad: 'Погрустить',
  thrill: 'Напряжение',
}

const MOOD_AFTER_LABELS: Record<CardMoodAfter, string> = {
  laughed: 'Веселый',
  cried: 'Плакал',
  enjoyed: 'Кайфанул',
  tense: 'Уставший',
  wasted_time: 'Зря потратил время',
}

function ratingPalette(value: number): { ring: string; glow: string; text: string } {
  if (value <= 3) return { ring: '#ef4444', glow: 'rgba(239,68,68,0.35)', text: '#fca5a5' }
  if (value <= 5) return { ring: '#f59e0b', glow: 'rgba(245,158,11,0.35)', text: '#fcd34d' }
  if (value <= 7) return { ring: '#84cc16', glow: 'rgba(132,204,22,0.35)', text: '#bef264' }
  return { ring: '#22c55e', glow: 'rgba(34,197,94,0.35)', text: '#86efac' }
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatCommentTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function authorName(comment: MovieCardComment): string {
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

type FollowingRatingRow = {
  user_id: string
  movie_card_id: number
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
  rating: number
  is_viewer?: boolean
}

function buildFollowingRatingDisplayRows(
  viewerRating: FollowingRatingRow | null | undefined,
  items: FollowingRatingRow[],
): FollowingRatingRow[] {
  const rows: FollowingRatingRow[] = []
  if (viewerRating != null) {
    rows.push({ ...viewerRating, is_viewer: true })
  }
  for (const row of items) {
    rows.push({ ...row, is_viewer: false })
  }
  return rows
}

type FollowingNamePick = {
  display_name: string | null
  first_name: string | null
  last_name: string | null
  username: string | null
}

function followingRowToProfileFields(row: FollowingRatingRow): FollowingNamePick {
  return {
    display_name: row.display_name,
    first_name: row.first_name,
    last_name: row.last_name,
    username: row.username,
  }
}

function followingRowDisplayName(row: FollowingRatingRow): string {
  if (row.is_viewer) return 'Вы'
  return displayNameFromProfile(followingRowToProfileFields(row))
}

function followingRowInitials(row: FollowingRatingRow): string {
  if (row.is_viewer) return 'В'
  const p = followingRowToProfileFields(row)
  return profileInitials({
    display_name: p.display_name,
    first_name: p.first_name,
    username: p.username,
  })
}

function movieCardAuthorOrNull(value: MovieCard): MovieCardCommentAuthor | null {
  const v = value as unknown as { card_author?: MovieCardCommentAuthor }
  return v.card_author ?? null
}

function movieCardWatchNotePlainText(value: MovieCard): string {
  const v = value as unknown as { watch_note?: unknown }
  const raw = v.watch_note
  return typeof raw === 'string' ? raw : ''
}

function CardAuthorAvatarLink({ author }: { author: MovieCardCommentAuthor }) {
  return (
    <Link
      to={`/u/${encodeURIComponent(author.id)}`}
      className="shrink-0 no-underline transition-opacity motion-safe:hover:opacity-90"
      aria-label={displayNameFromProfile(author)}
    >
      <Avatar src={author.photo_url ?? undefined} acronym={profileInitials(author)} size={28} />
    </Link>
  )
}

type MovieCardLocationState = { cardEntry?: string; fromFeed?: boolean } | null | undefined

export function MovieCardDetailPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const removeMovieCardRequest = useRemoveMovieCard()
  const { cardId } = useParams<{ cardId?: string }>()
  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)
  const [card, setCard] = useState<MovieCard | null>(null)
  const [comments, setComments] = useState<MovieCardComment[]>([])
  const [commentsNextCursor, setCommentsNextCursor] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)
  const [jumpBusy, setJumpBusy] = useState(false)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const [actionMenuOpen, setActionMenuOpen] = useState(false)
  const [highlightCommentId, setHighlightCommentId] = useState<number | null>(null)
  const [followingRatings, setFollowingRatings] = useState<FollowingRatingRow[] | null>(null)
  const [commentMentionPicker, setCommentMentionPicker] = useState<ActiveMentionQuery | null>(null)
  const [commentMentionHighlightIdx, setCommentMentionHighlightIdx] = useState(0)
  const commentRefs = useRef<Record<number, HTMLDivElement | null>>({})
  const commentTextAreaRef = useRef<HTMLTextAreaElement>(null)

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])

  const commentsById = useMemo(() => {
    const map = new Map<number, MovieCardComment>()
    comments.forEach((comment) => {
      map.set(comment.id, comment)
    })
    return map
  }, [comments])
  const palette = useMemo(() => ratingPalette(card?.rating ?? 1), [card?.rating])
  const isOwner =
    card != null && card.user_id != null && viewerId != null && card.user_id === viewerId
  const cardDeepLinkUrl = useMemo(
    () => (card != null ? buildMiniAppCardDeepLink(card.id) : null),
    [card],
  )
  const charsLeft = COMMENT_BODY_MAX_LEN - commentText.length
  const invalidCardId = parsedCardId == null

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

  const mentionRowsForCardDetail = useMemo((): MentionProfileRowInput[] => {
    const seen = new Set<string>()
    const out: MentionProfileRowInput[] = []
    const push = (r: MentionProfileRowInput) => {
      const k = mentionProfileKeyFromSlug(r.profile_slug)
      if (k.length === 0 || seen.has(k)) return
      seen.add(k)
      out.push(r)
    }
    if (card != null) {
      const author = movieCardAuthorOrNull(card)
      if (author != null) push(authorLikeToMentionRow(author))
    }
    for (const c of comments) push(authorLikeToMentionRow(c.author))
    for (const it of followingMentionItems) push(subscriptionToMentionRow(it))
    return out
  }, [card, comments, followingMentionItems])

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

  useEffect(() => {
    if (parsedCardId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = await getMovieCardById(parsedCardId)
        if (!alive) return
        setCard(item)
        setActionMenuOpen(false)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить карточку')
        }
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId])

  useEffect(() => {
    if (parsedCardId == null) return
    let alive = true
    queueMicrotask(() => {
      if (alive) setFollowingRatings(null)
    })
    void (async () => {
      try {
        const data = await getFollowingRatingsForCard(parsedCardId)
        if (!alive) return
        setFollowingRatings(
          buildFollowingRatingDisplayRows(data.viewer_rating ?? null, data.items),
        )
      } catch {
        if (!alive) return
        setFollowingRatings([])
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId])

  useEffect(() => {
    if (card == null || viewerId == null) return
    recordRecentCardView(viewerId, {
      id: card.id,
      film_title: card.film_title,
      film_poster_url: card.film_poster_url,
    })
    markGlobalFeedCardDetailOpened(card.id)
  }, [card, viewerId])

  const loadComments = useCallback(
    async (append: boolean) => {
      if (parsedCardId == null) return
      const cursor = append ? commentsNextCursor : null
      if (append && cursor == null) return

      setCommentsLoading(true)
      if (!append) {
        setCommentsError(null)
      }
      try {
        const page = await getMovieCardComments(parsedCardId, { cursor, limit: 20 })
        setComments((prev) => (append ? [...prev, ...page.items] : page.items))
        setCommentsNextCursor(page.next_cursor ?? null)
      } catch (e) {
        if (e instanceof ApiError) {
          setCommentsError(formatApiDetail(e.detail))
        } else {
          setCommentsError('Не удалось загрузить комментарии')
        }
      } finally {
        setCommentsLoading(false)
      }
    },
    [commentsNextCursor, parsedCardId]
  )

  useEffect(() => {
    if (parsedCardId == null || error != null) return
    let alive = true
    void (async () => {
      if (!alive) return
      await loadComments(false)
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId, error, loadComments])

  async function handleCreateComment() {
    if (parsedCardId == null || submitBusy) return
    const text = commentText.trim()
    if (text === '') return
    setSubmitBusy(true)
    setCommentsError(null)
    try {
      await createMovieCardComment(parsedCardId, {
        text,
        parent_comment_id: replyTo?.id ?? null,
      })
      await loadComments(false)
      setCommentText('')
      setCommentMentionPicker(null)
      setCommentMentionHighlightIdx(0)
      setReplyTo(null)
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setCommentsError(formatApiDetail(e.detail))
      } else {
        setCommentsError('Не удалось отправить комментарий')
      }
    } finally {
      setSubmitBusy(false)
    }
  }

  async function handleJumpToParent(parentCommentId: number) {
    if (parsedCardId == null || jumpBusy) return
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
        const page = await getMovieCardComments(parsedCardId, { cursor, limit: 20 })
        accumulated = [...accumulated, ...page.items]
        cursor = page.next_cursor ?? null
      }
      setComments(accumulated)
      setCommentsNextCursor(cursor)

      const found = accumulated.some((item) => item.id === parentCommentId)
      if (!found) {
        setCommentsError('Родительский комментарий не найден')
        return
      }
      window.requestAnimationFrame(() => {
        scrollToComment(parentCommentId)
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setCommentsError(formatApiDetail(e.detail))
      } else {
        setCommentsError('Не удалось загрузить родительский комментарий')
      }
    } finally {
      setJumpBusy(false)
    }
  }

  async function handleDeleteCard() {
    if (parsedCardId == null || deleteBusy) return
    const confirmed = window.confirm('Удалить карточку? Это действие нельзя отменить.')
    if (!confirmed) return

    setDeleteBusy(true)
    setError(null)
    setActionMenuOpen(false)
    try {
      await removeMovieCardRequest(parsedCardId)
      clearMyProfileBundleCache()
      void navigate('/profile')
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось удалить карточку')
      }
    } finally {
      setDeleteBusy(false)
    }
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] shadow-[0_1px_0_rgba(0,0,0,0.12)] backdrop-blur-md">
        <div className="flex items-center gap-2 px-3 py-2">
          <button
            type="button"
            onClick={() => {
              const st = location.state as MovieCardLocationState
              if (st?.cardEntry === 'telegram_start_param') {
                void navigate('/')
                return
              }
              void navigate(-1)
            }}
            className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) transition-transform duration-200 active:scale-90 motion-safe:hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_08%,transparent)]"
            aria-label="Назад"
          >
            ←
          </button>
          <span className="truncate text-sm font-medium tracking-tight text-(--tgui--hint_color)">
            {card?.film_title ?? 'Карточка'}
          </span>
          <span className="ml-auto" />
          {isOwner ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setActionMenuOpen((prev) => !prev)}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-(--tgui--divider_color) text-xl text-(--tgui--text_color)"
                aria-label="Действия с карточкой"
              >
                ⋯
              </button>
              {actionMenuOpen ? (
                <div className="filmony-detail-menu-pop absolute right-0 top-12 z-30 w-48 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2 shadow-xl ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)]">
                  <button
                    type="button"
                    onClick={() => {
                      setActionMenuOpen(false)
                      if (parsedCardId != null) {
                        void navigate(`/cards/${parsedCardId}/edit`)
                      }
                    }}
                    className="flex w-full items-center rounded-xl px-3 py-2 text-left text-base hover:bg-(--tgui--secondary_bg_color)"
                  >
                    Редактировать
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      void handleDeleteCard()
                    }}
                    disabled={deleteBusy}
                    className="mt-1 flex w-full items-center rounded-xl px-3 py-2 text-left text-base text-(--tgui--destructive_text_color) hover:bg-(--tgui--secondary_bg_color)"
                  >
                    {deleteBusy ? 'Удаление...' : 'Удалить'}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </header>

      <main className="mx-auto max-w-md px-3 pb-8 pt-3 sm:px-4">
        {loading ? <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p> : null}

        {invalidCardId ? (
          <div className="py-10 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">Некорректный id карточки</p>
            <Link to="/profile" className="mt-3 inline-block text-sm text-(--tgui--link_color)">
              Вернуться в профиль
            </Link>
          </div>
        ) : null}

        {error != null && !invalidCardId ? (
          <div className="py-10 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
            <Link to="/profile" className="mt-3 inline-block text-sm text-(--tgui--link_color)">
              Вернуться в профиль
            </Link>
          </div>
        ) : null}

        {!invalidCardId && !loading && error == null && card != null ? (
          <MentionProfileLookupProvider value={mentionRowsForCardDetail}>
          <MovieCardDetailLoadedBody
            card={card}
            palette={palette}
            cardDeepLinkUrl={cardDeepLinkUrl}
            isOwner={isOwner}
            viewerId={viewerId}
            followingRatings={followingRatings}
            comments={comments}
            commentsById={commentsById}
            commentsLoading={commentsLoading}
            commentsError={commentsError}
            commentsNextCursor={commentsNextCursor}
            commentText={commentText}
            replyTo={replyTo}
            submitBusy={submitBusy}
            jumpBusy={jumpBusy}
            charsLeft={charsLeft}
            highlightCommentId={highlightCommentId}
            commentRefs={commentRefs}
            commentTextAreaRef={commentTextAreaRef}
            insertReactionIntoComment={insertReactionIntoComment}
            loadComments={loadComments}
            handleCreateComment={handleCreateComment}
            handleJumpToParent={handleJumpToParent}
            onCommentTextChange={handleCommentTextChange}
            onCommentKeyDown={handleCommentDraftKeyDown}
            onCommentKeyUp={() => {
              const el = commentTextAreaRef.current
              if (el == null) return
              syncCommentMentionFromValue(
                el.value.slice(0, COMMENT_BODY_MAX_LEN),
                el.selectionStart ?? el.value.length,
              )
            }}
            onCommentSelect={() => {
              const el = commentTextAreaRef.current
              if (el == null) return
              syncCommentMentionFromValue(
                el.value.slice(0, COMMENT_BODY_MAX_LEN),
                el.selectionStart ?? el.value.length,
              )
            }}
            commentMentionPicker={commentMentionPicker}
            commentMentionHighlightIdx={commentMentionHighlightSafe}
            commentMentionFiltered={commentMentionFiltered}
            followingMentionItems={followingMentionItems}
            followingMentionQueryPending={followingForMentionsQuery.isPending}
            followingMentionQueryError={followingForMentionsQuery.isError}
            onPickCommentMention={pickCommentMention}
            onDismissCommentMention={() => {
              setCommentMentionPicker(null)
              setCommentMentionHighlightIdx(0)
            }}
            setReplyTo={setReplyTo}
            setCard={setCard}
            setComments={setComments}
          />
          </MentionProfileLookupProvider>
        ) : null}
      </main>
    </div>
  )
}

type MovieCardDetailLoadedBodyProps = {
  card: MovieCard
  palette: { ring: string; glow: string; text: string }
  cardDeepLinkUrl: string | null
  isOwner: boolean
  viewerId: string | null
  followingRatings: FollowingRatingRow[] | null
  comments: MovieCardComment[]
  commentsById: Map<number, MovieCardComment>
  commentsLoading: boolean
  commentsError: string | null
  commentsNextCursor: string | null
  commentText: string
  replyTo: { id: number; label: string } | null
  submitBusy: boolean
  jumpBusy: boolean
  charsLeft: number
  highlightCommentId: number | null
  commentRefs: MutableRefObject<Record<number, HTMLDivElement | null>>
  commentTextAreaRef: RefObject<HTMLTextAreaElement | null>
  insertReactionIntoComment: (reactionTypeId: number) => void
  loadComments: (append: boolean) => Promise<void>
  handleCreateComment: () => Promise<void>
  handleJumpToParent: (parentCommentId: number) => Promise<void>
  onCommentTextChange: (v: string) => void
  onCommentKeyDown: KeyboardEventHandler<HTMLTextAreaElement>
  onCommentKeyUp: () => void
  onCommentSelect: () => void
  commentMentionPicker: ActiveMentionQuery | null
  commentMentionHighlightIdx: number
  commentMentionFiltered: SubscriptionListItem[]
  followingMentionItems: SubscriptionListItem[]
  followingMentionQueryPending: boolean
  followingMentionQueryError: boolean
  onPickCommentMention: (slug: string) => void
  onDismissCommentMention: () => void
  setReplyTo: Dispatch<SetStateAction<{ id: number; label: string } | null>>
  setCard: Dispatch<SetStateAction<MovieCard | null>>
  setComments: Dispatch<SetStateAction<MovieCardComment[]>>
}

function MovieCardDetailLoadedBody({
  card,
  palette,
  cardDeepLinkUrl,
  isOwner,
  viewerId,
  followingRatings,
  comments,
  commentsById,
  commentsLoading,
  commentsError,
  commentsNextCursor,
  commentText,
  replyTo,
  submitBusy,
  jumpBusy,
  charsLeft,
  highlightCommentId,
  commentRefs,
  commentTextAreaRef,
  insertReactionIntoComment,
  loadComments,
  handleCreateComment,
  handleJumpToParent,
  onCommentTextChange,
  onCommentKeyDown,
  onCommentKeyUp,
  onCommentSelect,
  commentMentionPicker,
  commentMentionHighlightIdx,
  commentMentionFiltered,
  followingMentionItems,
  followingMentionQueryPending,
  followingMentionQueryError,
  onPickCommentMention,
  onDismissCommentMention,
  setReplyTo,
  setCard,
  setComments,
}: MovieCardDetailLoadedBodyProps) {
  const commentMentionAnchorRef = useRef<HTMLDivElement>(null)
  const commentMentionPopoverLayout = useMentionPopoverLayout(commentMentionPicker != null, commentMentionAnchorRef)
  const { openCompose } = useComposeFeedPost()
  const navigate = useNavigate()
  const location = useLocation()
  const fromFeed =
    typeof location.state === 'object' &&
    location.state !== null &&
    'fromFeed' in location.state &&
    Boolean((location.state as { fromFeed?: boolean }).fromFeed)
  const detailCardAuthor = movieCardAuthorOrNull(card)
  const watchNoteText = movieCardWatchNotePlainText(card)
  const showWatchNote = watchNoteText.trim().length > 0

  return (
          <div className="space-y-3">
            <div className="filmony-card-detail-panel-enter group/poster overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] shadow-[inset_0_1px_0_rgba(255,255,255,0.045)] contain-[paint]">
              <div className="relative w-full overflow-hidden bg-(--tgui--bg_color)">
                {card.film_poster_url ? (
                  <img
                    src={card.film_poster_url}
                    alt={card.film_title}
                    className="filmony-detail-poster-img block h-auto w-full max-w-full motion-safe:transition-transform motion-safe:duration-1100 motion-safe:ease-out motion-safe:group-hover/poster:scale-[1.02]"
                  />
                ) : (
                  <div className="flex min-h-40 items-center justify-center px-4 py-12 text-sm text-(--tgui--hint_color)">
                    Нет постера
                  </div>
                )}
                <div
                  className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-linear-to-t from-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] via-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_35%,transparent)] to-transparent"
                  aria-hidden
                />
                <div
                  className="absolute bottom-3 right-3 z-10 sm:bottom-4 sm:right-4"
                  style={{ '--filmony-rating-glow': palette.glow } as CSSProperties}
                >
                  <div
                    className="filmony-detail-rating-ring flex h-20 w-20 shrink-0 flex-col items-center justify-center gap-0.5 rounded-full border-[3px] bg-[color-mix(in_srgb,var(--filmony-void,#0a1018)_88%,transparent)] shadow-[0_12px_28px_rgba(0,0,0,0.35)] backdrop-blur-sm sm:h-21 sm:w-21"
                    style={{
                      borderColor: palette.ring,
                      color: palette.text,
                    }}
                  >
                    <span className="text-[9px] font-semibold uppercase leading-none tracking-[0.14em] text-(--tgui--hint_color)">
                      Оценка
                    </span>
                    <span className="text-[1.5rem] font-extrabold leading-none tabular-nums tracking-tight sm:text-[1.65rem]">
                      {formatRating(card.rating)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="px-3.5 pb-3 pt-4 sm:px-4">
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1 pr-1">
                    <Title level="2" weight="2" className="text-[1.15rem]! leading-snug! sm:text-[1.2rem]!">
                      {card.film_title}
                    </Title>
                    <div className="mt-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                      {detailCardAuthor != null ? <CardAuthorAvatarLink author={detailCardAuthor} /> : null}
                      <p className="min-w-0 text-xs font-medium tabular-nums text-(--tgui--hint_color) sm:text-sm">
                        {card.film_year ?? 'Год неизвестен'}
                      </p>
                    </div>
                    <FilmGenreChips genres={card.film_genres} size="md" className="mt-2" />
                    <FilmSynopsisBlock
                      shortDescription={card.film_short_description}
                      description={card.film_description}
                      className="mt-3"
                    />
                  </div>
                  <div className="flex shrink-0 items-center gap-0.5 pt-0.5">
                    <IconButton
                      type="button"
                      size="s"
                      mode="gray"
                      aria-label="Открыть страницу фильма на Кинопоиске"
                      onClick={() => openExternalUrl(kinopoiskTitleUrl(card.film_kinopoisk_id))}
                    >
                      <span className="relative z-1 flex h-[18px] min-w-[18px] items-center justify-center rounded-[4px] bg-[#ff6600] px-[3px] text-[8px] font-black leading-none tracking-tight text-white">
                        КП
                      </span>
                    </IconButton>
                    {cardDeepLinkUrl != null ? (
                      <IconButton
                        type="button"
                        size="s"
                        mode="gray"
                        aria-label="Скопировать ссылку на карточку"
                        onClick={() => {
                          void (async () => {
                            const ok = await copyTextToClipboard(cardDeepLinkUrl)
                            if (ok) {
                              safeHapticSuccess()
                            }
                          })()
                        }}
                      >
                        <Link2 className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
                      </IconButton>
                    ) : null}
                    {isOwner ? (
                      <FavoriteCardHeartButton
                        cardId={card.id}
                        isFavorite={card.is_favorite ?? false}
                        onFavoriteChange={(next) =>
                          setCard((prev) => (prev ? { ...prev, is_favorite: next } : prev))
                        }
                      />
                    ) : null}
                    {isOwner ? (
                      <IconButton
                        type="button"
                        size="s"
                        mode="gray"
                        aria-label="Поделиться карточкой"
                        onClick={() =>
                          void navigate(`/cards/${card.id}/share`, {
                            state: { shareOpenedFromCardDetail: true },
                          })
                        }
                      >
                        <Share2 className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
                      </IconButton>
                    ) : viewerId != null ? (
                      <IconButton
                        type="button"
                        size="s"
                        mode="gray"
                        aria-label="Взять за основу — создать свою карточку с этим тайтлом"
                        onClick={() => {
                          const qs = new URLSearchParams({ fromCard: String(card.id) })
                          if (fromFeed) qs.set('returnTo', 'feed')
                          void navigate(`/cards/new?${qs.toString()}`)
                        }}
                      >
                        <CopyPlus className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
                      </IconButton>
                    ) : null}
                  </div>
                </div>
                {card.user_id != null ? (
                  <div className="mt-3 min-w-0 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_55%,transparent)] pt-2.5">
                    <ReactionStrip
                      compact
                      compactTight
                      targetKind="movie_card"
                      targetId={card.id}
                      summary={card.reactions}
                      onSummaryChange={(next: ReactionSummary) =>
                        setCard((prev) => (prev ? { ...prev, reactions: next } : prev))
                      }
                    />
                  </div>
                ) : null}
              </div>
            </div>

            <section className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-1 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Теги</p>
              <div className="mt-2.5 flex flex-wrap gap-2">
                <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,var(--filmony-surface,#111b27))] px-3 py-1.5 text-xs font-medium text-(--tgui--text_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] transition duration-200 motion-safe:active:scale-[0.97]">
                  {COMPANY_LABELS[card.company]}
                </span>
                <span className="rounded-full border border-[color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] bg-transparent px-3 py-1.5 text-xs font-medium text-(--tgui--text_color) transition duration-200 motion-safe:active:scale-[0.97]">
                  {MOOD_BEFORE_LABELS[card.mood_before]}
                </span>
                <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_32%,var(--filmony-elevated,#182433))] px-3 py-1.5 text-xs font-semibold text-(--filmony-ink,#06090d) shadow-[0_1px_0_rgba(255,255,255,0.12)] transition duration-200 motion-safe:active:scale-[0.97]">
                  {MOOD_AFTER_LABELS[card.mood_after]}
                </span>
              </div>
              <p className="mt-3.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Свои теги</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {card.custom_tags.length > 0 ? (
                  card.custom_tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-lg border border-[color-mix(in_srgb,var(--tgui--divider_color)_90%,transparent)] bg-(--tgui--bg_color) px-2.5 py-1 text-xs transition duration-200 motion-safe:hover:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)] motion-safe:hover:shadow-[0_0_0_1px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] motion-safe:active:scale-[0.98]"
                    >
                      {tag}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-(--tgui--hint_color)">Пока нет собственных тегов</span>
                )}
              </div>
              {showWatchNote ? (
                <>
                  <p className="mt-3.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Заметка о просмотре</p>
                  <p className="mt-2 whitespace-pre-wrap wrap-break-word text-sm leading-relaxed text-(--tgui--text_color)">
                    <CommentBodyWithReactionTokens text={watchNoteText} />
                  </p>
                </>
              ) : null}
            </section>

            <section className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-2 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Друзья оценили</p>
              <p className="mt-1 text-[11px] leading-snug text-(--tgui--secondary_hint_color)">Сравнить с подписками.</p>
              {followingRatings == null ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Загрузка…</p>
              ) : followingRatings.length === 0 ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока некого показать.</p>
              ) : (
                <ul className="mt-3 list-none space-y-1.5 p-0">
                  {followingRatings.map((row: FollowingRatingRow) => {
                    const rp = ratingPalette(row.rating)
                    return (
                      <li key={row.movie_card_id}>
                        <Link
                          to={`/cards/${row.movie_card_id}`}
                          className="flex items-center gap-3 rounded-xl px-1 py-1.5 no-underline outline-none transition-colors duration-200 motion-safe:hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_06%,transparent)] ring-(--tgui--link_color) focus-visible:ring-2"
                        >
                          <Avatar
                            src={row.photo_url ?? undefined}
                            acronym={followingRowInitials(row)}
                            size={40}
                          />
                          <span className="min-w-0 flex-1 truncate text-sm font-medium text-(--tgui--text_color)">
                            {followingRowDisplayName(row)}
                          </span>
                          <span
                            className="shrink-0 text-lg font-semibold tabular-nums"
                            style={{ color: rp.text }}
                          >
                            {formatRating(row.rating)}
                          </span>
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </section>

            <section className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-3 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Комментарии</p>

              {replyTo != null ? (
                <div className="mt-2 flex items-center justify-between rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,var(--tgui--divider_color))] bg-(--tgui--bg_color) px-3 py-2 text-xs motion-safe:animate-[filmony-detail-fade-in_0.25s_ease-out_both]">
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
                      onChange={onCommentTextChange}
                      onKeyDown={onCommentKeyDown}
                      onKeyUp={onCommentKeyUp}
                      onSelect={onCommentSelect}
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
                              onClick={onDismissCommentMention}
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
                              {followingMentionQueryPending ? (
                                <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
                              ) : followingMentionQueryError ? (
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
                                  const selected = idx === commentMentionHighlightIdx
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
                                        onPickCommentMention(it.profile_slug)
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
                  <span className={`text-xs ${charsLeft < 20 ? 'text-(--tgui--destructive_text_color)' : 'text-(--tgui--hint_color)'}`}>
                    Осталось: {charsLeft}
                  </span>
                  <Button
                    size="s"
                    disabled={submitBusy || commentText.trim() === ''}
                    onClick={() => void handleCreateComment()}
                    className="motion-safe:transition motion-safe:duration-200 motion-safe:active:scale-[0.97]"
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
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока нет комментариев. Будьте первым.</p>
              ) : null}

              {comments.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {comments.map((comment) => {
                    const parent = comment.parent_comment_id != null ? commentsById.get(comment.parent_comment_id) ?? null : null
                    const parentCommentId = comment.parent_comment_id
                    return (
                      <div
                        key={comment.id}
                        ref={(element) => {
                          commentRefs.current[comment.id] = element
                        }}
                        className={`rounded-xl border bg-(--tgui--bg_color) p-3 motion-safe:transition-[border-color,box-shadow,transform] motion-safe:duration-300 ${
                          highlightCommentId === comment.id
                            ? 'border-(--tgui--link_color) shadow-[0_0_0_2px_color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] motion-safe:scale-[1.01]'
                            : 'border-(--tgui--divider_color) motion-safe:hover:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,var(--tgui--divider_color))]'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <Link to={`/u/${encodeURIComponent(comment.author.id)}`} className="no-underline">
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
                                >
                                  {authorName(comment)}
                                </Link>
                                <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(comment.created_at)}</span>
                              </div>
                              <div className="flex shrink-0 items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => setReplyTo({ id: comment.id, label: authorName(comment) })}
                                  className="inline-flex bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--link_color)"
                                >
                                  Ответить
                                </button>
                                {viewerId != null && comment.author.id === viewerId ? (
                                  <button
                                    type="button"
                                    onClick={() =>
                                      openCompose({
                                        sourceCommentId: comment.id,
                                        referencedMovieCardId: card.id,
                                      })
                                    }
                                    className="inline-flex bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--link_color)"
                                  >
                                    В ленту
                                  </button>
                                ) : null}
                              </div>
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
                                targetKind="movie_card_comment"
                                targetId={comment.id}
                                summary={comment.reactions}
                                onSummaryChange={(next: ReactionSummary) =>
                                  setComments((prev) =>
                                    prev.map((c) => (c.id === comment.id ? { ...c, reactions: next } : c))
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
                  onClick={() => {
                    void loadComments(true)
                  }}
                  className="mt-3 text-xs text-(--tgui--link_color)"
                  disabled={commentsLoading}
                >
                  Показать еще комментарии
                </button>
              ) : null}
            </section>
          </div>
  )
}
