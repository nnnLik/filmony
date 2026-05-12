import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useRef, useState, type MouseEventHandler } from 'react'
import { Link } from 'react-router-dom'

import { createMovieCardComment, listAllMovieCardComments, type WatchedInlinePickerItem } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import type { FeedMovieCard, MovieCardComment, ReactionSummary } from '../../api/profileTypes'
import { MentionProfileLookupProvider } from '../../context/MentionProfileLookupProvider'
import { authorLikeToMentionRow } from '../../lib/mentionProfileLookupUtils'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { CommentDraftSingleLineInput } from '../comments/CommentDraftMirrorField'
import { MovieCardInlinePickerButton } from '../comments/MovieCardInlinePickerButton'
import { CommentReactionTokenPicker } from '../comments/CommentReactionTokenPicker'
import { inlineMovieCardRefMapFromSnippets } from '../../lib/inlineMovieCardRefMap'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  movieCardRefTokenFromId,
  reactionTokenFromId,
} from '../../lib/commentReactionTokens'
import { movieCardCommentImageSrc } from '../../lib/movieCardCommentMedia'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import { FilmGenreChips } from '../films/FilmGenreChips'
import { ReactionStrip } from '../reactions/ReactionStrip'
import { IconChevronDown, IconSend } from './FeedCardIcons'
import { FeedRatingRing } from './FeedRatingRing'
import {
  authorLabel,
  commentAuthorDisplay,
  COMPANY_SHORT,
  feedCardSourceBadge,
  formatCommentTime,
  MOOD_AFTER_SHORT,
  MOOD_BEFORE_SHORT,
  snippetPreview,
} from './feedCardUtils'

export type FeedCardProps = {
  card: FeedMovieCard
  /** Id текущего пользователя из кэша профиля; для подсветки своих карточек */
  viewerUserId?: string | null
  onCommentsState: (
    cardId: number,
    next: { comments_count: number; comments_preview: MovieCardComment[] }
  ) => void
}

export function FeedCard({ card, viewerUserId = null, onCommentsState }: FeedCardProps) {
  const draftInputRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState('')
  const [draftInlineCardRefs, setDraftInlineCardRefs] = useState(
    () => new Map<number, { film_title: string; film_year: number | null }>(),
  )
  const [submitBusy, setSubmitBusy] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [commentsPreviewOpen, setCommentsPreviewOpen] = useState(false)
  const [reactionSync, setReactionSync] = useState(() => ({
    cardId: card.id,
    reactions: card.reactions,
  }))
  const [cardReaction, setCardReaction] = useState<ReactionSummary | undefined>(() => card.reactions)
  if (card.id !== reactionSync.cardId || card.reactions !== reactionSync.reactions) {
    setReactionSync({ cardId: card.id, reactions: card.reactions })
    setCardReaction(card.reactions)
  }

  const [previewSync, setPreviewSync] = useState(() => ({
    cardId: card.id,
    comments_preview: card.comments_preview,
  }))
  const [previewReactions, setPreviewReactions] = useState<Record<number, ReactionSummary>>({})
  const [panelComments, setPanelComments] = useState<MovieCardComment[]>([])
  const [panelLoading, setPanelLoading] = useState(false)
  const [panelError, setPanelError] = useState<string | null>(null)
  if (card.id !== previewSync.cardId || card.comments_preview !== previewSync.comments_preview) {
    setPreviewSync({ cardId: card.id, comments_preview: card.comments_preview })
    setPreviewReactions({})
  }

  const isOwnCard =
    viewerUserId != null && viewerUserId !== '' && card.user_id === viewerUserId
  /** Карточка с `is_favorite`: второй бейдж «Особая карточка» в шапке (свои и чужие в ленте). */
  const authorFavoriteRibbon = Boolean(card.is_favorite)
  const sourceBadgeText = useMemo(
    () => feedCardSourceBadge(card, viewerUserId ?? null),
    [card, viewerUserId],
  )
  const profileHref = `/u/${encodeURIComponent(card.user_id)}`
  const cardHref = `/cards/${card.id}`
  const name = authorLabel(card)
  useEffect(() => {
    let cancelled = false
    if (!commentsPreviewOpen || card.comments_count === 0) {
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

    void listAllMovieCardComments(card.id).then(
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
  }, [commentsPreviewOpen, card.id, card.comments_count])

  const previewCommentsById = useMemo(() => {
    const map = new Map<number, MovieCardComment>()
    panelComments.forEach((c) => {
      map.set(c.id, c)
    })
    return map
  }, [panelComments])

  const mergedPreviewAfterCreate = useCallback(
    (incoming: MovieCardComment) => {
      const nextCount = card.comments_count + 1
      const merged = [...card.comments_preview, incoming].sort((a, b) => a.id - b.id).slice(-3)
      onCommentsState(card.id, { comments_count: nextCount, comments_preview: merged })
      setCommentsPreviewOpen(true)
    },
    [card.comments_count, card.comments_preview, card.id, onCommentsState],
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
      setDraftInlineCardRefs(new Map())
      safeHapticSuccess()
    } catch (e) {
      setSubmitError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отправить')
    } finally {
      setSubmitBusy(false)
    }
  }, [card.id, draft, mergedPreviewAfterCreate])

  const remainder = card.custom_tags.length > 2 ? card.custom_tags.length - 2 : 0
  const shownTags = card.custom_tags.slice(0, 2)
  const charsLeft = COMMENT_BODY_MAX_LEN - draft.length

  const mentionProfileRows = useMemo(() => {
    const rows = [authorLikeToMentionRow(card.card_author)]
    for (const c of card.comments_preview) {
      rows.push(authorLikeToMentionRow(c.author))
    }
    for (const c of panelComments) {
      rows.push(authorLikeToMentionRow(c.author))
    }
    return rows
  }, [card.card_author, card.comments_preview, panelComments])

  const insertReactionToken = useCallback((reactionTypeId: number) => {
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
  }, [draft])

  const insertMovieCardInline = useCallback((row: WatchedInlinePickerItem) => {
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
  }, [draft])

  const stopCardNav: MouseEventHandler = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const stopCardNavKeepFocus: MouseEventHandler = (e) => {
    e.stopPropagation()
  }

  return (
    <MentionProfileLookupProvider value={mentionProfileRows}>
    <article
      data-testid={`feed-card-${card.id}`}
      className={`flex max-w-full flex-col gap-2 overflow-hidden rounded-2xl p-2.5 shadow-[0_10px_40px_-14px_rgba(0,0,0,0.45)] ${
        isOwnCard
          ? 'border-2 border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_42%,transparent)] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
          : 'border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
      }`}
    >
      <div className="mb-0.5 flex flex-wrap items-center gap-2 px-0.5">
        <span
          className="shrink-0 rounded-md border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_38%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-(--tgui--text_color)"
          title={
            isOwnCard
              ? 'Твоя карточка'
              : card.feed_source === 'subscriptions'
                ? 'Из подписок'
                : card.feed_source === 'subscribers'
                  ? 'Из подписчиков'
                  : card.feed_source === 'personal_affinity'
                    ? 'Похоже на ваши теги'
                    : card.feed_source === 'discovery'
                      ? 'Рекомендации'
                      : card.feed_source === 'own_cards'
                        ? 'Твоя карточка в ленте'
                        : card.feed_source === 'global'
                          ? 'Публичная лента'
                          : 'Источник в ленте'
          }
        >
          {sourceBadgeText}
        </span>
        {authorFavoriteRibbon ? (
          <span
            className="shrink-0 rounded-md border border-[color-mix(in_srgb,#ec4899_48%,transparent)] bg-[color-mix(in_srgb,#ec4899_16%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-pink-600 dark:text-pink-300"
            title={
              isOwnCard
                ? 'Вы отметили эту карточку как особую'
                : 'Автор отметил эту карточку как особую'
            }
          >
            Особая карточка
          </span>
        ) : null}
      </div>
      {/* Главная зона: постер отступает от краёв карточки, клик ведёт на страницу карточки */}
      <Link
        to={cardHref}
        state={{ fromFeed: true }}
        className="group relative isolate block w-full shrink-0 overflow-hidden rounded-xl bg-(--tgui--divider_color) no-underline ring-1 ring-(--tgui--divider_color) transition-shadow active:opacity-95 group-hover:ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)]"
        aria-label={`Открыть карточку «${card.film_title}»`}
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
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[3] bg-linear-to-t from-black/82 via-black/35 to-transparent pt-14 pb-2.5 pl-3 pr-19">
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
          <FeedRatingRing rating={card.rating} positionClassName="absolute right-2.5 top-2.5 z-[3]" />
        </div>
      </Link>

      {/* Мета: профиль (только аватар, имя в title) + теги — не накрываем overlay-ссылкой */}
      <div className="flex min-w-0 flex-col gap-1.5">
        <div className="flex min-w-0 items-center justify-between gap-1.5">
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

        <FilmGenreChips genres={card.film_genres} maxVisible={3} className="mt-0.5" />

        {card.watch_note != null && card.watch_note.trim() !== '' ? (
          <p className="line-clamp-4 text-[12px] leading-snug text-(--tgui--text_color)">
            <CommentBodyWithReactionTokens text={card.watch_note} className="text-[12px] leading-snug" />
          </p>
        ) : null}

        {(shownTags.length > 0 || remainder > 0) && (
          <div className="flex max-w-full flex-wrap items-center gap-0.5">
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

        {/* Один ряд: реакции слева, комментарии справа */}
        <div className="relative z-10 flex min-w-0 flex-col gap-1.5">
          <div className="flex min-w-0 items-center justify-between gap-2">
            <div className="min-w-0 flex-1 overflow-hidden py-px" onMouseDown={stopCardNav}>
              <ReactionStrip
                targetKind="movie_card"
                targetId={card.id}
                summary={cardReaction}
                onSummaryChange={setCardReaction}
                compact
              />
            </div>
            <div className="flex shrink-0 items-center gap-1 border-l border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] pl-2">
              <span
                title="Комментарии"
                className="max-w-[5.5rem] truncate text-[11px] font-medium leading-none text-(--tgui--hint_color) sm:max-w-none"
              >
                Комментарии
              </span>
              <span
                className="text-xs font-semibold tabular-nums leading-none text-(--tgui--text_color)"
                title="Всего комментариев к карточке"
              >
                {card.comments_count}
              </span>
              <button
                type="button"
                onMouseDown={stopCardNav}
                onClick={() => setCommentsPreviewOpen((open) => !open)}
                aria-expanded={commentsPreviewOpen}
                aria-label={
                  commentsPreviewOpen
                    ? 'Скрыть список комментариев и поле ввода'
                    : 'Показать все комментарии и написать ответ'
                }
                className="flex size-7 shrink-0 items-center justify-center rounded-md text-(--tgui--hint_color) transition-[background-color,color,transform] hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] hover:text-(--tgui--text_color) active:scale-95"
              >
                <IconChevronDown
                  className={`size-4 transition-transform duration-200 ${commentsPreviewOpen ? 'rotate-180' : ''}`}
                />
              </button>
            </div>
          </div>

          {commentsPreviewOpen ? (
            <div className="flex flex-col gap-2 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_55%,transparent)] pt-2">
              {card.comments_count > 0 ? (
                <div
                  className="max-h-[min(42vh,15rem)] min-h-30 overflow-y-auto overscroll-y-contain touch-pan-y space-y-1.5 pr-0.5 [-webkit-overflow-scrolling:touch]"
                  role="region"
                  aria-label="Комментарии к карточке"
                >
                  {panelLoading ? (
                    <p className="py-6 text-center text-xs text-(--tgui--hint_color)">Загрузка…</p>
                  ) : panelError != null ? (
                    <p className="text-xs text-(--tgui--destructive_text_color,#ef4444)">
                      {panelError}{' '}
                      <Link to={cardHref} state={{ fromFeed: true }} className="text-(--tgui--link_color) no-underline active:opacity-90">
                        Открыть карточку
                      </Link>
                    </p>
                  ) : panelComments.length === 0 ? (
                    <p className="text-xs text-(--tgui--hint_color)">
                      <Link to={cardHref} state={{ fromFeed: true }} className="text-(--tgui--link_color) no-underline active:opacity-90">
                        Открыть карточку
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
                            <Link to={authorHref} className="shrink-0 no-underline" aria-label={`Профиль: ${commentAuthorDisplay(comment)}`}>
                              <Avatar
                                src={comment.author.photo_url ?? undefined}
                                acronym={commentAuthorDisplay(comment).slice(0, 2).toUpperCase()}
                                size={24}
                              />
                            </Link>
                            <div className="min-w-0 flex-1">
                              <div className="flex min-w-0 items-center justify-between gap-2">
                                <div className="flex min-w-0 flex-wrap items-center gap-2">
                                  <span className="text-sm font-medium text-(--tgui--text_color)">{commentAuthorDisplay(comment)}</span>
                                  <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(comment.created_at)}</span>
                                </div>
                                <Link
                                  to={cardHref}
                                  state={{ fromFeed: true }}
                                  className="shrink-0 py-0 text-xs leading-none text-(--tgui--link_color) no-underline active:opacity-90"
                                  onMouseDown={stopCardNav}
                                >
                                  Ответить
                                </Link>
                              </div>

                              {parentCommentId != null ? (
                                <Link
                                  to={cardHref}
                                  state={{ fromFeed: true }}
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

                              {comment.image_url != null && comment.image_url.trim() !== '' ? (
                                <div className="mt-2 overflow-hidden rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
                                  <img
                                    src={movieCardCommentImageSrc(comment.image_url)}
                                    alt=""
                                    className="max-h-[min(55vw,12rem)] w-full object-cover object-center"
                                  />
                                </div>
                              ) : null}

                              {comment.text.trim() !== '' ? (
                                <p className="mt-1 text-[13px] leading-snug text-(--tgui--text_color)">
                                  <CommentBodyWithReactionTokens
                                    text={comment.text}
                                    className="whitespace-pre-wrap"
                                    inlineMovieCardRefs={inlineMovieCardRefMapFromSnippets(comment.referenced_movie_cards)}
                                  />
                                </p>
                              ) : null}
                              <div className="mt-1.5 flex min-w-0 flex-nowrap items-center gap-x-1 overflow-hidden" onMouseDown={stopCardNav}>
                                <ReactionStrip
                                  compact
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
                    })
                  )}
                </div>
              ) : (
                <p className="text-xs text-(--tgui--hint_color)">Пока нет комментариев. Будьте первым.</p>
              )}

              <div className="flex min-w-0 flex-col gap-1">
                <div className="relative z-10 flex min-w-0 items-stretch gap-1.5" onMouseDown={stopCardNavKeepFocus}>
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
            </div>
          ) : null}
        </div>
      </div>
    </article>
    </MentionProfileLookupProvider>
  )
}
