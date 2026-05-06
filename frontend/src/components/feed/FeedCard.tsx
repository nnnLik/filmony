import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState, type MouseEventHandler } from 'react'
import { Link } from 'react-router-dom'

import { createMovieCardComment } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import type { CardCompany, CardMoodAfter, CardMoodBefore, FeedMovieCard, MovieCardComment, ReactionSummary } from '../../api/profileTypes'
import { ReactionStrip } from '../reactions/ReactionStrip'

const COMPANY_SHORT: Record<CardCompany, string> = {
  alone: 'Один',
  partner: 'Пара',
  friends: 'Друзья',
  family: 'Семья',
}

const MOOD_BEFORE_SHORT: Record<CardMoodBefore, string> = {
  relax: 'Чилл',
  laugh: 'Юмор',
  sad: 'Грусть',
  thrill: 'Трилл',
}

const MOOD_AFTER_SHORT: Record<CardMoodAfter, string> = {
  laughed: 'Ржал',
  cried: 'Тэш',
  enjoyed: 'Топ',
  tense: 'Выжат',
  wasted_time: 'Зря',
}

function ratingPalette(value: number): { ring: string; glow: string; text: string; track: string } {
  if (value <= 3) {
    return { ring: '#ef4444', glow: 'rgba(239,68,68,0.35)', text: '#fca5a5', track: 'rgba(239,68,68,0.15)' }
  }
  if (value <= 5) {
    return { ring: '#f59e0b', glow: 'rgba(245,158,11,0.32)', text: '#fcd34d', track: 'rgba(245,158,11,0.14)' }
  }
  if (value <= 7) {
    return { ring: '#84cc16', glow: 'rgba(132,204,22,0.3)', text: '#bef264', track: 'rgba(132,204,22,0.12)' }
  }
  return { ring: '#22c55e', glow: 'rgba(34,197,94,0.32)', text: '#86efac', track: 'rgba(34,197,94,0.12)' }
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function authorLabel(card: FeedMovieCard): string {
  const a = card.card_author
  if (a.display_name && a.display_name.trim() !== '') {
    return a.display_name
  }
  if (a.username && a.username.trim() !== '') {
    return `@${a.username}`
  }
  const full = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Автор' : full
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

function commentAuthorDisplay(comment: MovieCardComment): string {
  const a = comment.author
  if (a.display_name && a.display_name.trim() !== '') {
    return a.display_name
  }
  if (a.username && a.username.trim() !== '') {
    return `@${a.username}`
  }
  const full = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Пользователь' : full
}

function snippetPreview(text: string): string {
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= 72) return compact
  return `${compact.slice(0, 69)}...`
}

/** Доля окружности (0–1) для шкалы 1–10 */
function ratingDashOffset(value: number): number {
  const clamped = Math.min(10, Math.max(1, value))
  const p = (clamped - 1) / 9
  return 219.99 * (1 - p)
}

function IconSend({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export type FeedCardProps = {
  card: FeedMovieCard
  onCommentsState: (
    cardId: number,
    next: { comments_count: number; comments_preview: MovieCardComment[] }
  ) => void
}

export function FeedCard({ card, onCommentsState }: FeedCardProps) {
  const [draft, setDraft] = useState('')
  const [submitBusy, setSubmitBusy] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [cardReaction, setCardReaction] = useState<ReactionSummary | undefined>(() => card.reactions)
  const [previewReactions, setPreviewReactions] = useState<Record<number, ReactionSummary>>({})

  const palette = useMemo(() => ratingPalette(card.rating), [card.rating])
  useEffect(() => {
    setCardReaction(card.reactions)
  }, [card.reactions])
  useEffect(() => {
    setPreviewReactions({})
  }, [card.id, card.comments_preview])
  const profileHref = `/u/${encodeURIComponent(card.user_id)}`
  const cardHref = `/cards/${card.id}`
  const name = authorLabel(card)
  const dashOffset = ratingDashOffset(card.rating)
  const previewCommentsById = useMemo(() => {
    const map = new Map<number, MovieCardComment>()
    card.comments_preview.forEach((c) => {
      map.set(c.id, c)
    })
    return map
  }, [card.comments_preview])

  const mergedPreviewAfterCreate = useCallback(
    (incoming: MovieCardComment) => {
      const nextCount = card.comments_count + 1
      const merged = [...card.comments_preview, incoming].sort((a, b) => a.id - b.id).slice(-3)
      onCommentsState(card.id, { comments_count: nextCount, comments_preview: merged })
    },
    [card.comments_count, card.comments_preview, card.id, onCommentsState]
  )

  const send = useCallback(async () => {
    const text = draft.trim()
    if (text.length === 0) return
    setSubmitBusy(true)
    setSubmitError(null)
    try {
      const created = await createMovieCardComment(card.id, { text })
      mergedPreviewAfterCreate(created)
      setDraft('')
    } catch (e) {
      setSubmitError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отправить')
    } finally {
      setSubmitBusy(false)
    }
  }, [card.id, draft, mergedPreviewAfterCreate])

  const remainder = card.custom_tags.length > 2 ? card.custom_tags.length - 2 : 0
  const shownTags = card.custom_tags.slice(0, 2)
  const charsLeft = 100 - draft.length

  const stopCardNav: MouseEventHandler = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <article
      data-testid={`feed-card-${card.id}`}
      className="flex max-w-full flex-col gap-3 overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] p-3 shadow-[0_10px_40px_-14px_rgba(0,0,0,0.45)]"
    >
      {/* Главная зона: постер отступает от краёв карточки, клик ведёт в карточку фильма */}
      <Link
        to={cardHref}
        className="group relative isolate block w-full shrink-0 overflow-hidden rounded-xl bg-(--tgui--divider_color) no-underline ring-1 ring-(--tgui--divider_color) transition-shadow active:opacity-95 group-hover:ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)]"
        aria-label={`Открыть «${card.film_title}»`}
      >
        <div className="relative aspect-2/3 max-h-[min(52vw,14rem)] w-full sm:max-h-64">
          {card.film_poster_url ? (
            <img
              src={card.film_poster_url}
              alt=""
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
            />
          ) : (
            <div className="flex h-full min-h-40 items-center justify-center px-4 text-center text-sm text-(--tgui--hint_color)">
              Нет постера
            </div>
          )}
          {/* Градиент снизу + заголовок на постере */}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-linear-to-t from-black/82 via-black/35 to-transparent pt-14 pb-2.5 pl-3 pr-19">
            <Title
              level="3"
              weight="2"
              className="line-clamp-2 text-[16px]! leading-tight text-white drop-shadow-sm"
            >
              {card.film_title}
              {card.film_year != null ? (
                <span className="font-normal text-white/72"> · {card.film_year}</span>
              ) : null}
            </Title>
          </div>
          {/* Оценка — круговой индикатор на постере */}
          <div
            className="absolute right-2.5 top-2.5 flex size-12 items-center justify-center rounded-full backdrop-blur-md select-none"
            style={{
              backgroundColor: palette.track,
              boxShadow: `0 6px 20px rgba(0,0,0,0.35), inset 0 0 20px ${palette.glow}`,
            }}
            aria-hidden
          >
            <svg viewBox="0 0 80 80" className="absolute size-12 -rotate-90">
              <circle cx="40" cy="40" fill="none" r="34" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
              <circle
                cx="40"
                cy="40"
                fill="none"
                r="34"
                stroke={palette.ring}
                strokeDasharray={219.99}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                strokeWidth="6"
                style={{ filter: `drop-shadow(0 0 6px ${palette.glow})` }}
              />
            </svg>
            <span className="relative text-[15px] font-extrabold tabular-nums text-white drop-shadow-sm">
              {formatRating(card.rating)}
            </span>
          </div>
        </div>
      </Link>

      {/* Мета: профиль (только аватар, имя в title) + теги — не накрываем overlay-ссылкой */}
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex min-w-0 items-center justify-between gap-2">
          <Link
            to={profileHref}
            className="relative z-10 flex shrink-0 rounded-full p-0.5 no-underline ring-1 ring-transparent transition-[box-shadow,ring-color] hover:ring-(--tgui--link_color) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--tgui--link_color)"
            title={name}
            aria-label={`Профиль: ${name}`}
          >
            <Avatar
              size={22}
              src={card.card_author.photo_url ?? undefined}
              acronym={(name.slice(0, 1) || '?').toUpperCase()}
            />
          </Link>
          <div className="flex min-w-0 flex-1 flex-wrap justify-end gap-1">
            <span className="rounded-full border border-transparent bg-[color-mix(in_srgb,var(--tgui--accent_text_color)_18%,transparent)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-(--tgui--text_color)">
              {COMPANY_SHORT[card.company]}
            </span>
            <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)] px-2 py-0.5 text-[10px] font-medium text-(--tgui--text_color)">
              {MOOD_BEFORE_SHORT[card.mood_before]}
            </span>
            <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_16%,transparent)] px-2 py-0.5 text-[10px] font-medium text-(--tgui--text_color)">
              {MOOD_AFTER_SHORT[card.mood_after]}
            </span>
          </div>
        </div>

        {(shownTags.length > 0 || remainder > 0) && (
          <div className="flex max-w-full flex-wrap items-center gap-1">
            {shownTags.map((tag) => (
              <span
                key={tag}
                className="max-w-[140px] truncate rounded-md border border-(--tgui--divider_color) bg-(--tgui--section_bg_color) px-1.5 py-0.5 text-[10px] text-(--tgui--hint_color)"
              >
                {tag}
              </span>
            ))}
            {remainder > 0 ? (
              <span className="text-[10px] font-semibold text-(--tgui--hint_color)">+{remainder}</span>
            ) : null}
          </div>
        )}

        <div className="relative z-10 mt-1" onMouseDown={stopCardNav}>
          <ReactionStrip
            targetKind="movie_card"
            targetId={card.id}
            summary={cardReaction}
            onSummaryChange={setCardReaction}
          />
        </div>

        {/* Комментарии: как на странице карточки; аватар (и имя) ведут в профиль автора */}
        <div className="relative z-10 mt-1">
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <span className="text-sm font-medium text-(--tgui--text_color)">Комментарии</span>
            <span
              className="text-xs tabular-nums text-(--tgui--hint_color)"
              title="Всего комментариев к карточке"
            >
              {card.comments_count}
            </span>
          </div>
          {card.comments_preview.length === 0 ? (
            <p className="text-xs text-(--tgui--hint_color)">Пока нет комментариев. Будьте первым.</p>
          ) : (
            <div className="space-y-2">
              {card.comments_preview.map((comment) => {
                const parentCommentId = comment.parent_comment_id
                const parent =
                  parentCommentId != null ? previewCommentsById.get(parentCommentId) ?? null : null

                const authorHref = `/u/${encodeURIComponent(comment.author.id)}`

                return (
                  <div
                    key={comment.id}
                    className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3"
                  >
                    <div className="flex items-start gap-2">
                      <Link to={authorHref} className="shrink-0 no-underline" aria-label={`Профиль: ${commentAuthorDisplay(comment)}`}>
                        <Avatar
                          src={comment.author.photo_url ?? undefined}
                          acronym={commentAuthorDisplay(comment).slice(0, 2).toUpperCase()}
                          size={28}
                        />
                      </Link>
                      <div className="min-w-0 flex-1">
                        <div className="flex min-w-0 flex-wrap items-center gap-2">
                          <span className="text-sm font-medium text-(--tgui--text_color)">{commentAuthorDisplay(comment)}</span>
                          <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(comment.created_at)}</span>
                        </div>

                        {parentCommentId != null ? (
                          <Link
                            to={cardHref}
                            className="mt-2 block w-full rounded-lg border-l-2 border-(--tgui--link_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-left no-underline active:opacity-90"
                          >
                            <p className="truncate text-xs font-medium text-(--tgui--link_color)">
                              {parent ? commentAuthorDisplay(parent) : 'Родительский комментарий'}
                            </p>
                            <p className="truncate text-xs text-(--tgui--hint_color)">
                              {parent ? snippetPreview(parent.text) : 'Откройте карточку, чтобы перейти к обсуждению'}
                            </p>
                          </Link>
                        ) : null}

                        <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-(--tgui--text_color)">{comment.text}</p>
                        <Link
                          to={cardHref}
                          className="mt-2 inline-block text-xs text-(--tgui--link_color) no-underline active:opacity-90"
                        >
                          Ответить
                        </Link>
                        <div className="mt-2" onMouseDown={stopCardNav}>
                          <ReactionStrip
                            targetKind="movie_card_comment"
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
              })}
            </div>
          )}
        </div>

        {/* Компактное поле — всегда видно */}
        <div className="relative z-10 flex min-w-0 items-stretch gap-1.5" onMouseDown={stopCardNav}>
          <input
            type="text"
            value={draft}
            disabled={submitBusy}
            maxLength={100}
            placeholder="Комментарий…"
            className="min-h-9 min-w-0 flex-1 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2 text-[14px] text-(--tgui--text_color) outline-none ring-(--tgui--link_color) placeholder:text-(--tgui--hint_color) focus-visible:border-transparent focus-visible:ring-2"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void send()
              }
            }}
            aria-label="Текст комментария"
          />
          <Button
            mode="filled"
            size="s"
            disabled={submitBusy || draft.trim().length === 0}
            type="button"
            className="min-h-9! min-w-9! shrink-0 px-0!"
            onClick={() => void send()}
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
    </article>
  )
}
