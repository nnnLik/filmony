import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import {
  createMovieCardComment,
  getMovieCardById,
  getMovieCardCommentReplies,
  getMovieCardComments,
} from '../api/cardApi'

type CardCompany = 'alone' | 'partner' | 'friends' | 'family'
type CardMoodBefore = 'relax' | 'laugh' | 'sad' | 'thrill'
type CardMoodAfter = 'laughed' | 'cried' | 'enjoyed' | 'tense' | 'wasted_time'

type MovieCardDetails = {
  id: number
  film_id: number
  film_kinopoisk_id: number
  film_genres: string[]
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
}

type MovieCardCommentAuthor = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
}

type MovieCardComment = {
  id: number
  movie_card_id: number
  parent_comment_id: number | null
  text: string
  created_at: string
  replies_count: number
  total_descendants_count: number
  author: MovieCardCommentAuthor
}

type MovieCardCommentPage = {
  items: MovieCardComment[]
  next_cursor: string | null
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

type CommentTreeNode = MovieCardComment & { children: CommentTreeNode[] }

function buildLoadedTree(
  items: MovieCardComment[],
  repliesByParentId: Record<number, MovieCardComment[]>
): CommentTreeNode[] {
  return items.map((item) => ({
    ...item,
    children: buildLoadedTree(repliesByParentId[item.id] ?? [], repliesByParentId),
  }))
}

type CommentNodeProps = {
  cardId: number
  node: CommentTreeNode
  depth: number
  onReply: (id: number, authorLabel: string) => void
  repliesByParentId: Record<number, MovieCardComment[]>
  nextCursorByParentId: Record<number, string | null>
  loadingByParentId: Record<number, boolean>
  expandedByParentId: Record<number, boolean>
  onToggleReplies: (comment: MovieCardComment) => void
  onLoadMoreReplies: (commentId: number) => void
}

function CommentNode({
  cardId,
  node,
  depth,
  onReply,
  repliesByParentId,
  nextCursorByParentId,
  loadingByParentId,
  expandedByParentId,
  onToggleReplies,
  onLoadMoreReplies,
}: CommentNodeProps) {
  const marginLeft = Math.min(depth * 14, 56)
  const isExpanded = expandedByParentId[node.id] ?? false
  const hasReplies = node.replies_count > 0
  const canOpenInline = node.total_descendants_count <= 4
  const children = repliesByParentId[node.id] ?? []
  const nextCursor = nextCursorByParentId[node.id] ?? null
  const loading = loadingByParentId[node.id] ?? false

  return (
    <div style={{ marginLeft }} className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
      <div className="flex items-start gap-2">
        <Link to={`/u/${encodeURIComponent(node.author.id)}`} className="no-underline">
          <Avatar
            src={node.author.photo_url ?? undefined}
            acronym={authorName(node).slice(0, 2).toUpperCase()}
            size={28}
          />
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Link to={`/u/${encodeURIComponent(node.author.id)}`} className="text-sm font-medium text-(--tgui--link_color) no-underline">
              {authorName(node)}
            </Link>
            <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(node.created_at)}</span>
          </div>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">{node.text}</p>
          <button
            type="button"
            onClick={() => onReply(node.id, authorName(node))}
            className="mt-2 text-xs text-(--tgui--link_color)"
          >
            Ответить
          </button>
          {hasReplies ? (
            canOpenInline ? (
              <button
                type="button"
                onClick={() => onToggleReplies(node)}
                className="ml-3 mt-2 text-xs text-(--tgui--link_color)"
              >
                {isExpanded ? 'Свернуть ответы' : `Показать ответы (${node.replies_count})`}
              </button>
            ) : (
              <Link
                to={`/cards/${cardId}/comments/${node.id}/thread`}
                className="ml-3 mt-2 inline-block text-xs text-(--tgui--link_color)"
              >
                Показать остальные ({node.total_descendants_count})
              </Link>
            )
          ) : null}
        </div>
      </div>
      {canOpenInline && isExpanded ? (
        <div className="mt-2 space-y-2">
          {loading ? <p className="text-xs text-(--tgui--hint_color)">Загрузка ответов…</p> : null}
          {children.map((child) => (
            <CommentNode
              key={child.id}
              cardId={cardId}
              node={{
                ...child,
                children: buildLoadedTree(repliesByParentId[child.id] ?? [], repliesByParentId),
              }}
              depth={depth + 1}
              onReply={onReply}
              repliesByParentId={repliesByParentId}
              nextCursorByParentId={nextCursorByParentId}
              loadingByParentId={loadingByParentId}
              expandedByParentId={expandedByParentId}
              onToggleReplies={onToggleReplies}
              onLoadMoreReplies={onLoadMoreReplies}
            />
          ))}
          {nextCursor ? (
            <button
              type="button"
              onClick={() => onLoadMoreReplies(node.id)}
              className="text-xs text-(--tgui--link_color)"
              disabled={loading}
            >
              Показать еще ответы
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

export function MovieCardDetailPage() {
  const navigate = useNavigate()
  const { cardId } = useParams<{ cardId?: string }>()
  const [card, setCard] = useState<MovieCardDetails | null>(null)
  const [rootComments, setRootComments] = useState<MovieCardComment[]>([])
  const [rootsNextCursor, setRootsNextCursor] = useState<string | null>(null)
  const [repliesByParentId, setRepliesByParentId] = useState<Record<number, MovieCardComment[]>>({})
  const [nextCursorByParentId, setNextCursorByParentId] = useState<Record<number, string | null>>({})
  const [expandedByParentId, setExpandedByParentId] = useState<Record<number, boolean>>({})
  const [loadingByParentId, setLoadingByParentId] = useState<Record<number, boolean>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])

  const tree = useMemo(
    () => buildLoadedTree(rootComments, repliesByParentId),
    [rootComments, repliesByParentId]
  )
  const fetchCommentReplies = getMovieCardCommentReplies as unknown as (
    cardId: number,
    commentId: number,
    params?: { cursor?: string | null; limit?: number }
  ) => Promise<MovieCardCommentPage>
  const palette = useMemo(() => ratingPalette(card?.rating ?? 1), [card?.rating])
  const charsLeft = 250 - commentText.length
  const invalidCardId = parsedCardId == null

  useEffect(() => {
    if (parsedCardId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = (await getMovieCardById(parsedCardId)) as unknown as MovieCardDetails
        if (!alive) return
        setCard(item)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить карточку фильма')
        }
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId])

  const loadRootComments = useCallback(
    async (append: boolean) => {
      if (parsedCardId == null) return
      const cursor = append ? rootsNextCursor : null
      if (append && cursor == null) return

      setCommentsLoading(true)
      if (!append) {
        setCommentsError(null)
      }
      try {
        const page = (await getMovieCardComments(parsedCardId, { cursor, limit: 20 })) as unknown as MovieCardCommentPage
        setRootComments((prev) => (append ? [...prev, ...page.items] : page.items))
        setRootsNextCursor(page.next_cursor ?? null)
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
    [parsedCardId, rootsNextCursor]
  )

  const loadReplies = useCallback(
    async (parentId: number, append: boolean) => {
      if (parsedCardId == null) return
      const cursor = append ? (nextCursorByParentId[parentId] ?? null) : null
      if (append && cursor == null) return

      setLoadingByParentId((prev) => ({ ...prev, [parentId]: true }))
      try {
        const page = await fetchCommentReplies(parsedCardId, parentId, { cursor, limit: 20 })
        setRepliesByParentId((prev) => ({
          ...prev,
          [parentId]: append ? [...(prev[parentId] ?? []), ...page.items] : page.items,
        }))
        setNextCursorByParentId((prev) => ({ ...prev, [parentId]: page.next_cursor ?? null }))
      } catch (e) {
        if (e instanceof ApiError) {
          setCommentsError(formatApiDetail(e.detail))
        } else {
          setCommentsError('Не удалось загрузить ответы')
        }
      } finally {
        setLoadingByParentId((prev) => ({ ...prev, [parentId]: false }))
      }
    },
    [fetchCommentReplies, nextCursorByParentId, parsedCardId]
  )

  useEffect(() => {
    if (parsedCardId == null || error != null) return
    let alive = true
    void (async () => {
      if (!alive) return
      setRepliesByParentId({})
      setNextCursorByParentId({})
      setExpandedByParentId({})
      await loadRootComments(false)
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId, error, loadRootComments])

  async function handleToggleReplies(comment: MovieCardComment) {
    const expanded = expandedByParentId[comment.id] ?? false
    if (expanded) {
      setExpandedByParentId((prev) => ({ ...prev, [comment.id]: false }))
      return
    }
    setExpandedByParentId((prev) => ({ ...prev, [comment.id]: true }))
    if ((repliesByParentId[comment.id] ?? []).length === 0) {
      await loadReplies(comment.id, false)
    }
  }

  async function handleCreateComment() {
    if (parsedCardId == null || submitBusy) return
    const text = commentText.trim()
    if (text === '') return
    setSubmitBusy(true)
    setCommentsError(null)
    try {
      const created = (await createMovieCardComment(parsedCardId, {
        text,
        parent_comment_id: replyTo?.id ?? null,
      })) as unknown as MovieCardComment
      if (replyTo == null) {
        setRootComments((prev) => [created, ...prev])
      } else {
        await loadReplies(replyTo.id, false)
      }
      await loadRootComments(false)
      setCommentText('')
      setReplyTo(null)
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

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center gap-2 px-3 py-2">
          <button
            type="button"
            onClick={() => {
              void navigate(-1)
            }}
            className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
            aria-label="Назад"
          >
            ←
          </button>
          <span className="truncate text-sm font-medium text-(--tgui--hint_color)">
            {card?.film_title ?? 'Карточка фильма'}
          </span>
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
            <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
              <div className="aspect-video w-full">
                {card.film_poster_url ? (
                  <img src={card.film_poster_url} alt={card.film_title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">Нет постера</div>
                )}
              </div>
              <div className="px-4 py-3">
                <Title level="2" weight="2">
                  {card.film_title}
                </Title>
                <p className="mt-1 text-sm text-(--tgui--hint_color)">{card.film_year ?? 'Год неизвестен'}</p>
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
              <div className="flex gap-2">
                <Button stretched mode="gray" disabled>
                  Пригласить друзей (mock)
                </Button>
                <Button stretched mode="gray" disabled>
                  Рекомендовать (mock)
                </Button>
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Друзья оценили</p>
              <div className="mt-3 space-y-2 text-sm text-(--tgui--hint_color)">
                <p>Аня — 10</p>
                <p>Максим — 8</p>
                <p>Катя — 9</p>
              </div>
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
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.currentTarget.value)}
                  rows={4}
                  maxLength={250}
                  placeholder="Напишите комментарий..."
                  className="w-full resize-y rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2 text-sm outline-none"
                />
                <div className="mt-1 flex items-center justify-between">
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

              {!commentsLoading && tree.length === 0 ? (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока нет комментариев. Будьте первым.</p>
              ) : null}

              {tree.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {tree.map((node) => (
                    <CommentNode
                      key={node.id}
                      cardId={parsedCardId ?? node.movie_card_id}
                      node={node}
                      depth={0}
                      onReply={(id, label) => setReplyTo({ id, label })}
                      repliesByParentId={repliesByParentId}
                      nextCursorByParentId={nextCursorByParentId}
                      loadingByParentId={loadingByParentId}
                      expandedByParentId={expandedByParentId}
                      onToggleReplies={(comment) => {
                        void handleToggleReplies(comment)
                      }}
                      onLoadMoreReplies={(commentId) => {
                        void loadReplies(commentId, true)
                      }}
                    />
                  ))}
                </div>
              ) : null}

              {rootsNextCursor ? (
                <button
                  type="button"
                  onClick={() => {
                    void loadRootComments(true)
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
