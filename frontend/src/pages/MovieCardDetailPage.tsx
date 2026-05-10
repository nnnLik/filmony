import { Avatar, Button, IconButton, Title } from '@telegram-apps/telegram-ui'
import { CopyPlus, Link2, Share2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { createMovieCardComment, getFollowingRatingsForCard, getMovieCardById, getMovieCardComments } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile } from '../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MovieCard,
  MovieCardComment,
  ReactionSummary,
} from '../api/profileTypes'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'
import { copyTextToClipboard } from '../lib/copyTextToClipboard'
import { safeHapticSuccess } from '../lib/safeHaptic'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  reactionTokenFromId,
} from '../lib/commentReactionTokens'
import { buildMiniAppCardDeepLink } from '../lib/miniAppCardDeepLink'
import { recordRecentCardView } from '../lib/recentCardViews'
import { CommentBodyWithReactionTokens } from '../components/comments/CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from '../components/comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../components/comments/CommentReactionTokenPicker'
import { ReactionStrip } from '../components/reactions/ReactionStrip'
import { FavoriteCardHeartButton } from '../components/cards/FavoriteCardHeartButton'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { useRemoveMovieCard } from '../hooks/useRemoveMovieCard'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'

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

type MovieCardLocationState = { cardEntry?: string } | null | undefined

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

  const insertReactionIntoComment = useCallback(
    (reactionTypeId: number) => {
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
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
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
            className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
            aria-label="Назад"
          >
            ←
          </button>
          <span className="truncate text-sm font-medium text-(--tgui--hint_color)">
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
                <div className="absolute right-0 top-12 z-30 w-48 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2 shadow-xl">
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

      <main className="mx-auto max-w-md px-4 py-4">
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
          <div className="space-y-4">
            <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) contain-[paint]">
              <div className="aspect-video w-full">
                {card.film_poster_url ? (
                  <img src={card.film_poster_url} alt={card.film_title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">Нет постера</div>
                )}
              </div>
              <div className="px-4 pb-3 pt-3">
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <Title level="2" weight="2">
                      {card.film_title}
                    </Title>
                    <div className="mt-1 flex min-w-0 items-center gap-2">
                      {card.card_author != null ? (
                        <Link
                          to={`/u/${encodeURIComponent(card.card_author.id)}`}
                          className="shrink-0 no-underline"
                          aria-label={displayNameFromProfile(card.card_author)}
                        >
                          <Avatar
                            src={card.card_author.photo_url ?? undefined}
                            acronym={profileInitials(card.card_author)}
                            size={28}
                          />
                        </Link>
                      ) : null}
                      <p className="min-w-0 text-sm text-(--tgui--hint_color)">
                        {card.film_year ?? 'Год неизвестен'}
                      </p>
                    </div>
                    <FilmGenreChips genres={card.film_genres} size="md" className="mt-2" />
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
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
                        onClick={() => void navigate(`/cards/new?fromCard=${card.id}`)}
                      >
                        <CopyPlus className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
                      </IconButton>
                    ) : null}
                  </div>
                </div>
                {card.user_id != null ? (
                  <div className="mt-2.5 min-w-0">
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

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Твоя оценка</p>
              <div className="mt-3 flex items-center justify-center">
                <div
                  className="relative flex h-28 w-28 items-center justify-center rounded-full border-4 text-4xl font-extrabold"
                  style={{
                    borderColor: palette.ring,
                    color: palette.text,
                    boxShadow: `0 0 0 6px ${palette.glow}, inset 0 0 24px ${palette.glow}`,
                  }}
                >
                  {formatRating(card.rating)}
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Теги</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-[#1e3a5f] px-3 py-1.5 text-xs text-white">{COMPANY_LABELS[card.company]}</span>
                <span className="rounded-full bg-[#0f172a] px-3 py-1.5 text-xs text-white">
                  {MOOD_BEFORE_LABELS[card.mood_before]}
                </span>
                <span className="rounded-full bg-[#1d4ed8] px-3 py-1.5 text-xs text-white">
                  {MOOD_AFTER_LABELS[card.mood_after]}
                </span>
              </div>
              <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">Свои теги</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {card.custom_tags.length > 0 ? (
                  card.custom_tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1 text-xs"
                    >
                      {tag}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-(--tgui--hint_color)">Пока нет собственных тегов</span>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Друзья оценили</p>
              <p className="mt-1 text-xs text-(--tgui--hint_color)">Сравнить с подписками.</p>
              {followingRatings == null ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Загрузка…</p>
              ) : followingRatings.length === 0 ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока некого показать.</p>
              ) : (
                <ul className="mt-3 list-none space-y-3 p-0">
                  {followingRatings.map((row: FollowingRatingRow) => {
                    const rp = ratingPalette(row.rating)
                    return (
                      <li key={row.user_id}>
                        <Link
                          to={`/u/${encodeURIComponent(row.user_id)}`}
                          className="flex items-center gap-3 rounded-xl no-underline outline-none ring-(--tgui--link_color) focus-visible:ring-2"
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

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Комментарии</p>

              {replyTo != null ? (
                <div className="mt-2 flex items-center justify-between rounded-lg bg-(--tgui--bg_color) px-3 py-2 text-xs">
                  <span className="text-(--tgui--hint_color)">Ответ для: {replyTo.label}</span>
                  <button type="button" onClick={() => setReplyTo(null)} className="text-(--tgui--link_color)">
                    отменить
                  </button>
                </div>
              ) : null}

              <div className="mt-3">
                <div className="flex gap-2">
                  <CommentDraftMultiline
                    ref={commentTextAreaRef}
                    value={commentText}
                    onChange={setCommentText}
                    disabled={submitBusy}
                    rows={4}
                    maxLength={COMMENT_BODY_MAX_LEN}
                    placeholder="Напишите комментарий..."
                  />
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
                  <Button size="s" disabled={submitBusy || commentText.trim() === ''} onClick={() => void handleCreateComment()}>
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
                        className={`rounded-xl border bg-(--tgui--bg_color) p-3 transition ${
                          highlightCommentId === comment.id
                            ? 'border-(--tgui--link_color) shadow-[0_0_0_1px_var(--tgui--link_color)]'
                            : 'border-(--tgui--divider_color)'
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
                              <button
                                type="button"
                                onClick={() => setReplyTo({ id: comment.id, label: authorName(comment) })}
                                className="inline-flex shrink-0 bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--link_color)"
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
        ) : null}
      </main>
    </div>
  )
}
