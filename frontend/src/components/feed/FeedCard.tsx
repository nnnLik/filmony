import { Avatar, Title } from '@telegram-apps/telegram-ui'
import { Music } from 'lucide-react'
import { useCallback, useMemo, useRef, useState, type MouseEventHandler } from 'react'
import { Link, useNavigate } from 'react-router'

import { createMovieCardComment, listAllMovieCardComments, type WatchedInlinePickerItem } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import type { FeedMovieCard, MovieCardComment, ReactionSummary } from '../../api/profileTypes'
import {
  movieCardPrimaryPoster,
  movieCardPrimaryTitle,
  movieCardReleaseCompactSuffix,
} from '../../lib/movieCardDisplay'
import { MentionProfileLookupProvider } from '../../context/MentionProfileLookupProvider'
import { authorLikeToMentionRow } from '../../lib/mentionProfileLookupUtils'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { EngagementCommentsRow } from './EngagementCommentsRow'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  movieCardRefTokenFromId,
  reactionTokenFromId,
} from '../../lib/commentReactionTokens'
import { toggleSpoilerAtSelection } from '../../lib/spoilerTokens'
import { hasMeaningfulCardRating } from '../../lib/ratingDisplay'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import { useFeedCardAuthorBadges } from '../../hooks/useFeedCardAuthorBadges'
import { useFeedInlineCommentsPanel } from '../../hooks/useFeedInlineCommentsPanel'
import { useCommentScrollHighlight } from '../../hooks/useCommentScrollHighlight'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { FilmGenreChips } from '../films/FilmGenreChips'
import { DirectorChip } from '../films/DirectorChip'
import { FranchiseChip } from '../films/FranchiseChip'
import { CardCategoryChip } from '../cards/CardCategoryChip'
import { PlannedCardBadge } from '../cards/PlannedCardBadge'
import { ContrarianBadge } from '../gamification/ContrarianBadge'
import { FeedRatingRing } from './FeedRatingRing'
import {
  authorLabel,
  COMPANY_SHORT,
  MOOD_AFTER_SHORT,
  MOOD_BEFORE_SHORT,
  ratingPalette,
} from './feedCardUtils'
import { FeedExplainabilityChip } from './FeedExplainabilityChip'
import { MovieCardAudioPlayer } from '../cards/MovieCardAudioPlayer'
import { MovieCardRatingAudioVisualizer } from '../cards/MovieCardRatingAudioVisualizer'
import { useFeedCardGlobalAudio } from '../../hooks/useFeedCardGlobalAudio'
import { useFullscreenImageActivator } from '../../hooks/useFullscreenImageActivator'

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
  const navigate = useNavigate()
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
  if (card.id !== previewSync.cardId || card.comments_preview !== previewSync.comments_preview) {
    setPreviewSync({ cardId: card.id, comments_preview: card.comments_preview })
    setPreviewReactions({})
  }

  const listAllComments = useCallback(
    (cardId: number) => listAllMovieCardComments(cardId),
    [],
  )
  const {
    panelComments,
    panelLoading,
    panelError,
    previewCommentsById,
  } = useFeedInlineCommentsPanel<MovieCardComment>({
    postId: card.id,
    commentsCount: card.comments_count,
    open: commentsPreviewOpen,
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

  const isOwnCard =
    viewerUserId != null && viewerUserId !== '' && card.user_id === viewerUserId
  const isPlannedCard = card.is_planned === true
  /** Карточка с `is_favorite`: второй бейдж «Особая карточка» в шапке (свои и чужие в ленте). */
  const authorFavoriteRibbon = Boolean(card.is_favorite)
  const hasAttachedAudio = card.audio_url != null && card.audio_url.trim() !== ''
  const feedAudio = useFeedCardGlobalAudio()
  const audioUrlTrimmed = (card.audio_url ?? '').trim()
  const ratingRingPalette = useMemo(() => ratingPalette(card.rating), [card.rating])
  const isThisCardActive = feedAudio.playingCardId === card.id
  const playerPaused = !isThisCardActive || feedAudio.paused
  const profileHref = `/u/${encodeURIComponent(card.user_id)}`
  const cardHref = `/cards/${card.id}`
  const name = authorLabel(card)
  const primaryTitle = movieCardPrimaryTitle(card)
  const primaryPoster = movieCardPrimaryPoster(card)
  const releaseSuffix = movieCardReleaseCompactSuffix(card)
  const navigateToCard = useCallback(() => {
    void navigate(cardHref, { state: { fromFeed: true } })
  }, [navigate, cardHref])
  const posterFullscreen = useFullscreenImageActivator({
    enabled: true,
    imageSrc: primaryPoster ?? '',
    imageAlt: primaryTitle ? `Постер: ${primaryTitle}` : 'Постер карточки',
    onSingleNavigate: navigateToCard,
  })

  const panelCommentAuthorIds = useMemo(
    () => panelComments.map((comment) => comment.author.id),
    [panelComments],
  )
  const { knowledgeByOwnerId, streakByUserId } = useFeedCardAuthorBadges({
    scopeKey: `movie_card:${card.id}`,
    tasteQuizOwnerIds: isOwnCard ? [] : [card.user_id],
    streakUserIds: [card.user_id],
    panelCommentAuthorIds,
  })

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

  const remainder =
    !isPlannedCard && card.custom_tags.length > 2 ? card.custom_tags.length - 2 : 0
  const shownTags = isPlannedCard ? [] : card.custom_tags.slice(0, 2)
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
        <FeedExplainabilityChip variant="card" card={card} viewerUserId={viewerUserId} />
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
        {isPlannedCard ? <PlannedCardBadge variant="ribbon" /> : null}
        {hasAttachedAudio ? (
          <span
            role="img"
            aria-label="К карточке прикреплено аудио"
            title="К карточке прикреплено аудио"
            className="inline-flex shrink-0 items-center justify-center rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_48%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_16%,transparent)] px-1.5 py-0.5 text-(--tgui--text_color)"
          >
            <Music className="block size-3.5" strokeWidth={2.25} aria-hidden />
          </span>
        ) : null}
        <CardCategoryChip category={card.category} className="max-w-[min(100%,10rem)] shrink-0" />
      </div>
      {/* Главная зона: постер — кликом открываем карточку; аудио-кнопки вне ссылки */}
      <div className="group relative isolate block w-full shrink-0 overflow-hidden rounded-xl bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color) transition-shadow active:opacity-95 group-hover:ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)]">
        <div
          {...posterFullscreen.bindings}
          role="link"
          tabIndex={0}
          className="block w-full cursor-pointer rounded-xl no-underline outline-offset-4 outline-(--tgui--link_color) focus-visible:outline-2"
          aria-label={`Открыть карточку «${primaryTitle}»`}
        >
          <div className="relative w-full overflow-hidden rounded-xl bg-(--tgui--divider_color)">
            {primaryPoster ? (
              <img
                src={primaryPoster}
                alt=""
                loading="lazy"
                draggable={false}
                decoding="async"
                className="pointer-events-none block h-auto w-full max-w-none bg-(--tgui--divider_color) transition-transform duration-300 motion-safe:origin-top motion-safe:group-hover:scale-[1.02]"
              />
            ) : (
              <div className="flex min-h-40 w-full items-center justify-center px-4 py-8 text-center text-sm text-(--tgui--hint_color)">
                Нет постера
              </div>
            )}
            <div className="pointer-events-none absolute inset-x-0 bottom-0 z-3 bg-linear-to-t from-black/82 via-black/35 to-transparent pt-14 pb-2.5 pl-3 pr-19">
              <Title
                level="3"
                weight="2"
                className="line-clamp-2 text-[16px]! leading-tight text-white drop-shadow-sm"
              >
                {primaryTitle}
                {releaseSuffix != null ? (
                  <span className="font-normal text-white/72"> · {releaseSuffix}</span>
                ) : null}
              </Title>
            </div>
            {hasMeaningfulCardRating(card) ? (
              <div className="pointer-events-none absolute right-2.5 top-2.5 z-3">
                <div className="relative flex size-12 items-center justify-center">
                  {hasAttachedAudio && isThisCardActive ? (
                    <MovieCardRatingAudioVisualizer
                      audio={feedAudio.audioRef.current}
                      audioUrl={audioUrlTrimmed}
                      ringColor={ratingRingPalette.ring}
                      compact
                    />
                  ) : null}
                  <FeedRatingRing
                    rating={card.rating}
                    positionClassName="relative z-10"
                  />
                </div>
              </div>
            ) : null}
            {isOwnCard ? (
              <div className="pointer-events-none absolute left-2.5 top-2.5 z-3">
                <ContrarianBadge
                  rating={card.rating}
                  communityAvgRating={card.community_avg_rating}
                  isContrarian={card.is_contrarian}
                />
              </div>
            ) : null}
          </div>
        </div>
        {posterFullscreen.overlay}
        {hasAttachedAudio ? (
          <div className="pointer-events-auto absolute bottom-3 right-3 z-10">
            <MovieCardAudioPlayer
              cardId={card.id}
              audioUrl={audioUrlTrimmed}
              variant="compact"
              feedGlobal={{
                paused: playerPaused,
                onToggle: () => {
                  feedAudio.toggleCardAudio(card.id, audioUrlTrimmed)
                },
              }}
            />
          </div>
        ) : null}
      </div>

      {/* Мета: профиль (только аватар, имя в title) + теги — не накрываем overlay-ссылкой */}
      <div className="flex min-w-0 flex-col gap-1.5">
        <div className="flex min-w-0 items-center justify-between gap-1.5">
          <div className="flex shrink-0 items-center gap-1.5">
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
            <TasteQuizCommentAuthorBadge
              knowledgeByAuthor={knowledgeByOwnerId}
              authorId={card.user_id}
              viewerId={viewerUserId}
            />
            <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={card.user_id} />
          </div>
          <div className="flex min-w-0 flex-1 flex-wrap justify-end gap-1">
            <span className="rounded-full border border-transparent bg-[color-mix(in_srgb,var(--tgui--accent_text_color)_18%,transparent)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-(--tgui--text_color)">
              {COMPANY_SHORT[card.company]}
            </span>
            {!isPlannedCard ? (
              <>
                <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)] px-2 py-0.5 text-[10px] font-medium text-(--tgui--text_color)">
                  {MOOD_BEFORE_SHORT[card.mood_before]}
                </span>
                <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_16%,transparent)] px-2 py-0.5 text-[10px] font-medium text-(--tgui--text_color)">
                  {MOOD_AFTER_SHORT[card.mood_after]}
                </span>
              </>
            ) : null}
          </div>
        </div>

        {card.film_primary_director_kinopoisk_id != null &&
        card.film_primary_director_name != null &&
        card.film_primary_director_name.trim() !== '' ? (
          <DirectorChip
            kinopoiskId={card.film_primary_director_kinopoisk_id}
            name={card.film_primary_director_name}
            className="mt-0.5"
          />
        ) : null}

        {card.film_franchise_key != null &&
        card.film_franchise_label != null &&
        card.film_franchise_label.trim() !== '' ? (
          <FranchiseChip
            franchiseKey={card.film_franchise_key}
            label={card.film_franchise_label}
            className="mt-0.5"
          />
        ) : null}

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

        <EngagementCommentsRow
          commentsCount={card.comments_count}
          commentsPreviewOpen={commentsPreviewOpen}
          onTogglePreview={() => setCommentsPreviewOpen((open) => !open)}
          reactionTargetKind="movie_card"
          reactionTargetId={card.id}
          reactionSummary={cardReaction}
          onReactionChange={setCardReaction}
          panelComments={panelComments}
          previewCommentsById={previewCommentsById}
          panelLoading={panelLoading}
          panelError={panelError}
          detailHref={cardHref}
          detailLinkState={{ fromFeed: true }}
          viewerUserId={viewerUserId}
          knowledgeByAuthor={knowledgeByOwnerId}
          streakByUserId={streakByUserId}
          previewReactions={previewReactions}
          onPreviewReactionChange={(commentId, next) =>
            setPreviewReactions((prev) => ({ ...prev, [commentId]: next }))
          }
          commentReactionTargetKind="movie_card_comment"
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
          stopNav={stopCardNav}
          stopNavKeepFocus={stopCardNavKeepFocus}
          detailFallbackLabel="Открыть карточку"
        />
      </div>
    </article>
    </MentionProfileLookupProvider>
  )
}
