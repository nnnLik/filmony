import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import {
  createMovieCardComment,
  getMovieCardById,
  getMovieCardCommentReplies,
} from '../api/cardApi'

type CardCompany = 'alone' | 'partner' | 'friends' | 'family'
type CardMoodBefore = 'relax' | 'laugh' | 'sad' | 'thrill'
type CardMoodAfter = 'laughed' | 'cried' | 'enjoyed' | 'tense' | 'wasted_time'

type MovieCard = {
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

type ThreadNodeProps = {
  node: CommentTreeNode
  depth: number
  repliesByParentId: Record<number, MovieCardComment[]>
  nextCursorByParentId: Record<number, string | null>
  loadingByParentId: Record<number, boolean>
  expandedByParentId: Record<number, boolean>
  onToggleReplies: (comment: MovieCardComment) => void
  onLoadMoreReplies: (commentId: number) => void
  onReply: (id: number, label: string) => void
}

function ThreadNode({
  node,
  depth,
  repliesByParentId,
  nextCursorByParentId,
  loadingByParentId,
  expandedByParentId,
  onToggleReplies,
  onLoadMoreReplies,
  onReply,
}: ThreadNodeProps) {
  const marginLeft = Math.min(depth * 14, 56)
  const hasReplies = node.replies_count > 0
  const isExpanded = expandedByParentId[node.id] ?? false
  const children = repliesByParentId[node.id] ?? []
  const nextCursor = nextCursorByParentId[node.id] ?? null
  const loading = loadingByParentId[node.id] ?? false

  return (
    <div style={{ marginLeft }} className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
      <div className="flex items-start gap-2">
        <Link to={`/u/${encodeURIComponent(node.author.id)}`} className="no-underline">
          <Avatar src={node.author.photo_url ?? undefined} acronym={authorName(node).slice(0, 2).toUpperCase()} size={28} />
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Link to={`/u/${encodeURIComponent(node.author.id)}`} className="text-sm font-medium text-(--tgui--link_color) no-underline">
              {authorName(node)}
            </Link>
            <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(node.created_at)}</span>
          </div>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">{node.text}</p>
          <button type="button" onClick={() => onReply(node.id, authorName(node))} className="mt-2 text-xs text-(--tgui--link_color)">
            Ответить
          </button>
          {hasReplies ? (
            <button type="button" onClick={() => onToggleReplies(node)} className="ml-3 mt-2 text-xs text-(--tgui--link_color)">
              {isExpanded ? 'Свернуть ответы' : `Показать ответы (${node.replies_count})`}
            </button>
          ) : null}
        </div>
      </div>

      {isExpanded ? (
        <div className="mt-2 space-y-2">
          {loading ? <p className="text-xs text-(--tgui--hint_color)">Загрузка ответов…</p> : null}
          {children.map((child) => (
            <ThreadNode
              key={child.id}
              node={{ ...child, children: buildLoadedTree(repliesByParentId[child.id] ?? [], repliesByParentId) }}
              depth={depth + 1}
              repliesByParentId={repliesByParentId}
              nextCursorByParentId={nextCursorByParentId}
              loadingByParentId={loadingByParentId}
              expandedByParentId={expandedByParentId}
              onToggleReplies={onToggleReplies}
              onLoadMoreReplies={onLoadMoreReplies}
              onReply={onReply}
            />
          ))}
          {nextCursor ? (
            <button type="button" onClick={() => onLoadMoreReplies(node.id)} className="text-xs text-(--tgui--link_color)" disabled={loading}>
              Показать еще ответы
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

export function MovieCardCommentThreadPage() {
  const navigate = useNavigate()
  const { cardId, commentId } = useParams<{ cardId?: string; commentId?: string }>()
  const [card, setCard] = useState<MovieCard | null>(null)
  const [threadRootReplies, setThreadRootReplies] = useState<MovieCardComment[]>([])
  const [rootCursor, setRootCursor] = useState<string | null>(null)
  const [repliesByParentId, setRepliesByParentId] = useState<Record<number, MovieCardComment[]>>({})
  const [nextCursorByParentId, setNextCursorByParentId] = useState<Record<number, string | null>>({})
  const [expandedByParentId, setExpandedByParentId] = useState<Record<number, boolean>>({})
  const [loadingByParentId, setLoadingByParentId] = useState<Record<number, boolean>>({})
  const [loading, setLoading] = useState(false)
  const [threadLoading, setThreadLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [threadError, setThreadError] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])
  const parsedCommentId = useMemo(() => {
    if (commentId == null) return null
    const value = Number(commentId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [commentId])
  const invalidParams = parsedCardId == null || parsedCommentId == null
  const charsLeft = 250 - commentText.length
  const tree = useMemo(() => buildLoadedTree(threadRootReplies, repliesByParentId), [threadRootReplies, repliesByParentId])

  const loadRootReplies = useCallback(
    async (append: boolean) => {
      if (parsedCardId == null || parsedCommentId == null) return
      const cursor = append ? rootCursor : null
      if (append && cursor == null) return
      setThreadLoading(true)
      try {
        const page = (await getMovieCardCommentReplies(parsedCardId, parsedCommentId, { cursor, limit: 20 })) as unknown as MovieCardCommentPage
        setThreadRootReplies((prev) => (append ? [...prev, ...page.items] : page.items))
        setRootCursor(page.next_cursor ?? null)
      } catch (e) {
        if (e instanceof ApiError) {
          setThreadError(formatApiDetail(e.detail))
        } else {
          setThreadError('Не удалось загрузить ветку')
        }
      } finally {
        setThreadLoading(false)
      }
    },
    [parsedCardId, parsedCommentId, rootCursor]
  )

  const loadReplies = useCallback(
    async (parentId: number, append: boolean) => {
      if (parsedCardId == null) return
      const cursor = append ? (nextCursorByParentId[parentId] ?? null) : null
      if (append && cursor == null) return
      setLoadingByParentId((prev) => ({ ...prev, [parentId]: true }))
      try {
        const page = (await getMovieCardCommentReplies(parsedCardId, parentId, { cursor, limit: 20 })) as unknown as MovieCardCommentPage
        setRepliesByParentId((prev) => ({
          ...prev,
          [parentId]: append ? [...(prev[parentId] ?? []), ...page.items] : page.items,
        }))
        setNextCursorByParentId((prev) => ({ ...prev, [parentId]: page.next_cursor ?? null }))
      } catch (e) {
        if (e instanceof ApiError) {
          setThreadError(formatApiDetail(e.detail))
        } else {
          setThreadError('Не удалось загрузить ответы')
        }
      } finally {
        setLoadingByParentId((prev) => ({ ...prev, [parentId]: false }))
      }
    },
    [nextCursorByParentId, parsedCardId]
  )

  useEffect(() => {
    if (parsedCardId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = (await getMovieCardById(parsedCardId)) as unknown as MovieCard
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

  useEffect(() => {
    if (invalidParams || error != null) return
    setThreadError(null)
    setRepliesByParentId({})
    setNextCursorByParentId({})
    setExpandedByParentId({})
    void loadRootReplies(false)
  }, [invalidParams, error, loadRootReplies])

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
    setThreadError(null)
    try {
      await createMovieCardComment(parsedCardId, {
        text,
        parent_comment_id: replyTo?.id ?? parsedCommentId,
      })
      await loadRootReplies(false)
      if (replyTo != null) {
        await loadReplies(replyTo.id, false)
      }
      setCommentText('')
      setReplyTo(null)
    } catch (e) {
      if (e instanceof ApiError) {
        setThreadError(formatApiDetail(e.detail))
      } else {
        setThreadError('Не удалось отправить комментарий')
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
          <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Ветка комментариев</span>
        </div>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        {invalidParams ? (
          <p className="text-sm text-(--tgui--destructive_text_color)">Некорректные параметры ветки</p>
        ) : null}
        {loading ? <p className="text-sm text-(--tgui--hint_color)">Загрузка…</p> : null}
        {error ? <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p> : null}

        {!invalidParams && !loading && !error ? (
          <div className="space-y-3">
            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <Title level="3" weight="2">
                {card?.film_title ?? 'Карточка фильма'}
              </Title>
              <p className="mt-1 text-xs text-(--tgui--hint_color)">Полная ветка для комментария #{parsedCommentId}</p>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Ответить в этой ветке</p>
              {replyTo ? (
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
                  placeholder="Напишите ответ..."
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
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Ответы</p>
              {threadError ? <p className="mt-2 text-sm text-(--tgui--destructive_text_color)">{threadError}</p> : null}
              {threadLoading ? <p className="mt-2 text-sm text-(--tgui--hint_color)">Загрузка ответов…</p> : null}
              {!threadLoading && tree.length === 0 ? (
                <p className="mt-2 text-sm text-(--tgui--hint_color)">Пока нет ответов в этой ветке.</p>
              ) : null}
              {tree.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {tree.map((node) => (
                    <ThreadNode
                      key={node.id}
                      node={node}
                      depth={0}
                      repliesByParentId={repliesByParentId}
                      nextCursorByParentId={nextCursorByParentId}
                      loadingByParentId={loadingByParentId}
                      expandedByParentId={expandedByParentId}
                      onToggleReplies={(comment) => {
                        void handleToggleReplies(comment)
                      }}
                      onLoadMoreReplies={(parentId) => {
                        void loadReplies(parentId, true)
                      }}
                      onReply={(id, label) => setReplyTo({ id, label })}
                    />
                  ))}
                </div>
              ) : null}
              {rootCursor ? (
                <button type="button" onClick={() => void loadRootReplies(true)} className="mt-2 text-xs text-(--tgui--link_color)" disabled={threadLoading}>
                  Показать еще ответы
                </button>
              ) : null}
            </section>
          </div>
        ) : null}
      </main>
    </div>
  )
}
