import { Avatar, Button, IconButton, Title } from '@telegram-apps/telegram-ui'
import { CopyPlus, Link2, Share2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type Dispatch,
  type RefObject,
  type SetStateAction,
} from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'

import './movieCardDetailAnimations.css'

import {
  createMovieCardComment as submitMovieCardCommentApi,
  deleteMovieCardComment,
  getFilmById,
  getFollowingRatingsForCard,
  getMovieCardById,
  getMovieCardComments,
  updateMovieCardComment,
} from '../api/cardApi'
import { uploadMovieCardCommentImage } from '../api/movieCardCommentImageApi'
import type { WatchedInlinePickerItem } from '../api/watchedInlinePickerTypes'
import { getUserSubscriptions } from '../api/profileApi'
import type { SubscriptionListItem } from '../api/profileTypes'
import { ApiError, formatApiDetail } from '../api/client'
import { useAuthStatus } from '../auth/useAuthStatus'
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
import { formatRating, hasMeaningfulCardRating, ratingPalette } from '../lib/ratingDisplay'
import { copyTextToClipboard } from '../lib/copyTextToClipboard'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { TasteQuizCommentAuthorBadge } from '../components/tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../components/streaks/RatingStreakAuthorBadge'
import { WatchingNowAuthorBadge } from '../components/watchparty/WatchingNowAuthorBadge'
import type { TasteQuizKnowledgeBatchItem } from '../api/tasteQuizTypes'
import type { StreakBatchItem } from '../api/streaksTypes'
import type { WatchingNowBatchItem } from '../api/watchPartyTypes'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useWatchingNowOfUsers } from '../hooks/useWatchingNowOfUsers'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { COMMENT_BODY_MAX_LEN } from '../lib/commentReactionTokens'
import {
  authorLikeToMentionRow,
  mentionProfileKeyFromSlug,
  type MentionProfileRowInput,
} from '../lib/mentionProfileLookupUtils'
import { subscriptionToMentionRow } from '../lib/subscriptionToMentionRow'
import type { ActiveMentionQuery } from '../lib/feedMentionCompose'
import { buildMiniAppCardDeepLink } from '../lib/miniAppCardDeepLink'
import {
  movieCardHasKinopoiskLink,
  movieCardPrimaryPoster,
  movieCardPrimarySummary,
  movieCardPrimaryTitle,
  movieCardReleasePrimaryLabel,
} from '../lib/movieCardDisplay'
import { kinopoiskTitleUrlFromCard, openExternalUrl } from '../lib/openExternalUrl'
import { onWatchCtaClick } from '../lib/openFilmWatchInBrowser'
import { markGlobalFeedCardDetailOpened } from '../lib/globalFeedViewedIds'
import { recordRecentCardView } from '../lib/recentCardViews'
import { watchlistOverlapAnchorFromMovieCard } from '../lib/watchlistOverlapUtils'
import { CommentBodyWithReactionTokens } from '../components/comments/CommentBodyWithReactionTokens'
import { CommentThreadSection } from '../components/comments/CommentThreadSection'
import { ReactionStrip } from '../components/reactions/ReactionStrip'
import { FavoriteCardHeartButton } from '../components/cards/FavoriteCardHeartButton'
import { PlannedCardBadge } from '../components/cards/PlannedCardBadge'
import { PlannedWatchPartnersList } from '../components/cards/PlannedWatchPartnersList'
import { ContrarianBadge } from '../components/gamification/ContrarianBadge'
import { WatchlistOverlapAnchorBanner } from '../components/watchlist/WatchlistOverlapSection'
import { MovieCardAudioPlayer } from '../components/cards/MovieCardAudioPlayer'
import { MovieCardRatingAudioVisualizer } from '../components/cards/MovieCardRatingAudioVisualizer'
import { CardCategoryChip } from '../components/cards/CardCategoryChip'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { FilmCatalogMetadata } from '../components/films/FilmCatalogMetadata'
import { FilmTrailerIconButton } from '../components/films/FilmPassportInline'
import { DirectorChip } from '../components/films/DirectorChip'
import { FranchiseChip } from '../components/films/FranchiseChip'
import { OscarReleaseYearLabel } from '../components/films/OscarReleaseYearLabel'
import { primaryFilmAwardBadge } from '../lib/filmAwardBadgeDisplay'
import { FollowingRatingsPanel } from '../components/social/FollowingRatingsPanel'
import { FilmCollectionsStrip } from '../components/collections/FilmCollectionsStrip'
import { getFilmCollections } from '../api/collectionsApi'
import type { CollectionSummary } from '../api/collectionsTypes'
import { filmCollectionsQueryKey } from '../lib/collectionQueryKeys'
import {
  buildFollowingRatingDisplayRows,
  type FollowingRatingRow,
} from '../lib/followingRatingsDisplay'
import { FilmSynopsisBlock } from '../components/films/FilmSynopsisBlock'
import { useRemoveMovieCard } from '../hooks/useRemoveMovieCard'
import { usePaginatedComments } from '../hooks/usePaginatedComments'
import { useCommentScrollHighlight } from '../hooks/useCommentScrollHighlight'
import { useCommentJumpToParent } from '../hooks/useCommentJumpToParent'
import { useCommentDraftEditor } from '../hooks/useCommentDraftEditor'
import { commentAuthorLabel } from '../lib/commentDisplay'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { movieCardCommentDerivedFields } from '../lib/movieCardCommentDerivedFields'
import type { OpenComposeFeedPostPayload } from '../compose/feedComposeTypes'
import { useComposeFeedPost } from '../compose/useComposeFeedPost'
import { useFullscreenImageActivator } from '../hooks/useFullscreenImageActivator'

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

function plannedCardRateHref(card: MovieCard): string {
  return `/cards/new?fromCard=${encodeURIComponent(String(card.id))}&intent=rate`
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
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const location = useLocation()
  const removeMovieCardRequest = useRemoveMovieCard()
  const { cardId } = useParams<{ cardId?: string }>()
  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)
  const [card, setCard] = useState<MovieCard | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [commentImageUrl, setCommentImageUrl] = useState<string | null>(null)
  const [commentImageUploadBusy, setCommentImageUploadBusy] = useState(false)
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [editBusy, setEditBusy] = useState(false)
  const [deleteCommentBusyId, setDeleteCommentBusyId] = useState<number | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const [actionMenuOpen, setActionMenuOpen] = useState(false)
  const [followingRatings, setFollowingRatings] = useState<FollowingRatingRow[] | null>(null)
  const commentImageFileInputRef = useRef<HTMLInputElement>(null)

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])

  const commentsEnabled = parsedCardId != null && error == null

  const {
    comments,
    setComments,
    commentsNextCursor,
    setCommentsNextCursor,
    commentsById,
    commentsLoading,
    commentsError,
    setCommentsError,
    loadComments,
  } = usePaginatedComments<MovieCardComment>({
    enabled: commentsEnabled,
    mode: 'page',
    fetchPage: useCallback(
      ({ cursor, limit }) => {
        if (parsedCardId == null) {
          return Promise.reject(new Error('missing card id'))
        }
        return getMovieCardComments(parsedCardId, { cursor, limit })
      },
      [parsedCardId],
    ),
  })

  const { highlightCommentId, setCommentRef, scrollToComment } = useCommentScrollHighlight()

  const { jumpBusy, handleJumpToParent } = useCommentJumpToParent({
    comments,
    commentsById,
    commentsNextCursor,
    setComments,
    setCommentsNextCursor,
    setCommentsError,
    fetchPage: useCallback(
      ({ cursor, limit }) => {
        if (parsedCardId == null) {
          return Promise.reject(new Error('missing card id'))
        }
        return getMovieCardComments(parsedCardId, { cursor, limit })
      },
      [parsedCardId],
    ),
    scrollToComment,
  })

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

  const {
    commentText,
    commentDraftInlineCardRefs,
    commentTextAreaRef,
    commentMentionAnchorRef,
    commentMentionPicker,
    commentMentionHighlightIdx,
    commentMentionFiltered,
    commentMentionPopoverLayout,
    charsLeft,
    handleCommentTextChange,
    handleCommentDraftKeyDown,
    syncCommentMentionFromValue,
    pickCommentMention,
    dismissCommentMention,
    insertReactionIntoComment,
    insertMovieCardIntoComment,
    toggleSpoilerInComment,
    resetDraft,
  } = useCommentDraftEditor({
    followingMentionItems,
    disabled: submitBusy || commentImageUploadBusy,
  })

  const tasteQuizOwnerIds = useMemo(() => {
    const ids = new Set<string>()
    if (card?.user_id != null && card.user_id !== viewerId) {
      ids.add(card.user_id)
    }
    for (const comment of comments) {
      ids.add(comment.author.id)
    }
    return [...ids]
  }, [card, viewerId, comments])
  const streakUserIds = useMemo(() => {
    const ids = new Set<string>()
    if (card?.user_id != null) {
      ids.add(card.user_id)
    }
    for (const comment of comments) {
      ids.add(comment.author.id)
    }
    return [...ids]
  }, [card, comments])
  const { knowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(tasteQuizOwnerIds, {
    enabled: tasteQuizOwnerIds.length > 0,
  })
  const { streakByUserId } = useRatingStreaksOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
  })
  const { watchingByUserId } = useWatchingNowOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  const palette = useMemo(() => ratingPalette(card?.rating ?? 1), [card?.rating])
  const isOwner =
    card != null && card.user_id != null && viewerId != null && card.user_id === viewerId
  const cardDeepLinkUrl = useMemo(
    () => (card != null ? buildMiniAppCardDeepLink(card.id) : null),
    [card],
  )
  const invalidCardId = parsedCardId == null

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
    if (auth.kind !== 'ready') {
      queueMicrotask(() => setFollowingRatings(null))
      return
    }
    if (parsedCardId == null || card?.is_planned === true) {
      queueMicrotask(() => {
        setFollowingRatings(card?.is_planned === true ? [] : null)
      })
      return
    }
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
  }, [auth.kind, parsedCardId, card?.is_planned])

  useEffect(() => {
    if (card == null || viewerId == null) return
    recordRecentCardView(viewerId, {
      id: card.id,
      film_title: movieCardPrimaryTitle(card),
      film_poster_url: movieCardPrimaryPoster(card),
    })
    markGlobalFeedCardDetailOpened(card.id)
  }, [card, viewerId])

  async function handleCreateComment() {
    if (parsedCardId == null || submitBusy) return
    const text = commentText.trim()
    const img = (commentImageUrl ?? '').trim()
    if (text === '' && img === '') return
    setSubmitBusy(true)
    setCommentsError(null)
    try {
      await submitMovieCardCommentApi(parsedCardId, {
        text,
        parent_comment_id: replyTo?.id ?? null,
        image_url: img === '' ? null : img,
      })
      await loadComments(false)
      resetDraft()
      setCommentImageUrl(null)
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

  function handleCancelEdit() {
    setEditingCommentId(null)
    setEditText('')
  }

  async function handleSaveEdit(commentId: number, imageUrl: string | null) {
    if (parsedCardId == null || editBusy) return
    const text = editText.trim()
    if (text === '' && (imageUrl == null || imageUrl.trim() === '')) return
    setEditBusy(true)
    setCommentsError(null)
    try {
      const updated = await updateMovieCardComment(parsedCardId, commentId, {
        text,
        image_url: imageUrl,
      })
      setComments((prev) => prev.map((c) => (c.id === commentId ? updated : c)))
      handleCancelEdit()
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setCommentsError(formatApiDetail(e.detail))
      } else {
        setCommentsError('Не удалось сохранить комментарий')
      }
    } finally {
      setEditBusy(false)
    }
  }

  async function handleDeleteComment(commentId: number) {
    if (parsedCardId == null || deleteCommentBusyId != null) return
    const confirmed = window.confirm('Удалить комментарий? Ответы на него тоже будут удалены.')
    if (!confirmed) return
    setDeleteCommentBusyId(commentId)
    setCommentsError(null)
    try {
      await deleteMovieCardComment(parsedCardId, commentId)
      if (editingCommentId === commentId) handleCancelEdit()
      await loadComments(false)
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setCommentsError(formatApiDetail(e.detail))
      } else {
        setCommentsError('Не удалось удалить комментарий')
      }
    } finally {
      setDeleteCommentBusyId(null)
    }
  }

  const handlePickCommentImage = useCallback(() => {
    commentImageFileInputRef.current?.click()
  }, [])

  const handleCommentImageFileChange = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file == null) return
    setCommentImageUploadBusy(true)
    setCommentsError(null)
    try {
      const url = await uploadMovieCardCommentImage(file)
      setCommentImageUrl(url)
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setCommentsError(formatApiDetail(e.detail))
      } else {
        setCommentsError('Не удалось загрузить изображение')
      }
    } finally {
      setCommentImageUploadBusy(false)
    }
  }, [setCommentsError])

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
              if (st?.cardEntry === 'telegram_start_param' || location.key === 'default') {
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
            {card != null ? movieCardPrimaryTitle(card) : 'Карточка'}
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
                        void navigate(
                          `/cards/${parsedCardId}/${card?.is_planned === true ? 'edit-planned' : 'edit'}`,
                        )
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
            setCommentRef={setCommentRef}
            commentTextAreaRef={commentTextAreaRef}
            commentMentionAnchorRef={commentMentionAnchorRef}
            commentMentionPopoverLayout={commentMentionPopoverLayout}
            insertReactionIntoComment={insertReactionIntoComment}
            toggleSpoilerInComment={toggleSpoilerInComment}
            insertMovieCardIntoComment={insertMovieCardIntoComment}
            commentDraftInlineCardRefs={commentDraftInlineCardRefs}
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
            commentMentionHighlightIdx={commentMentionHighlightIdx}
            commentMentionFiltered={commentMentionFiltered}
            followingMentionItems={followingMentionItems}
            followingMentionQueryPending={followingForMentionsQuery.isPending}
            followingMentionQueryError={followingForMentionsQuery.isError}
            onPickCommentMention={pickCommentMention}
            onDismissCommentMention={dismissCommentMention}
            setReplyTo={setReplyTo}
            setCard={setCard}
            setComments={setComments}
            commentImageUrl={commentImageUrl}
            setCommentImageUrl={setCommentImageUrl}
            commentImageUploadBusy={commentImageUploadBusy}
            commentImageFileInputRef={commentImageFileInputRef}
            handlePickCommentImage={handlePickCommentImage}
            handleCommentImageFileChange={(event) => {
              void handleCommentImageFileChange(event)
            }}
            editingCommentId={editingCommentId}
            editText={editText}
            setEditText={setEditText}
            editBusy={editBusy}
            deleteCommentBusyId={deleteCommentBusyId}
            onStartEditComment={(comment) => {
              setEditingCommentId(comment.id)
              setEditText(comment.text)
              setReplyTo(null)
            }}
            onCancelEditComment={handleCancelEdit}
            onSaveEditComment={handleSaveEdit}
            onDeleteComment={(commentId) => {
              void handleDeleteComment(commentId)
            }}
            tasteQuizKnowledgeByAuthor={knowledgeByOwnerId}
            streakByUserId={streakByUserId}
            watchingByUserId={watchingByUserId}
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
  setCommentRef: (commentId: number, element: HTMLDivElement | null) => void
  commentTextAreaRef: RefObject<HTMLTextAreaElement | null>
  commentMentionAnchorRef: RefObject<HTMLDivElement | null>
  commentMentionPopoverLayout: { top: number; left: number; width: number; maxHeight: number } | null
  insertReactionIntoComment: (reactionTypeId: number) => void
  toggleSpoilerInComment: () => void
  insertMovieCardIntoComment: (row: WatchedInlinePickerItem) => void
  commentDraftInlineCardRefs: ReadonlyMap<number, { film_title: string; film_year: number | null }>
  loadComments: (append: boolean) => Promise<void>
  handleCreateComment: () => Promise<void>
  handleJumpToParent: (parentCommentId: number) => Promise<void>
  onCommentTextChange: (v: string) => void
  onCommentKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>
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
  commentImageUrl: string | null
  setCommentImageUrl: Dispatch<SetStateAction<string | null>>
  commentImageUploadBusy: boolean
  commentImageFileInputRef: RefObject<HTMLInputElement | null>
  handlePickCommentImage: () => void
  handleCommentImageFileChange: (event: ChangeEvent<HTMLInputElement>) => void
  editingCommentId: number | null
  editText: string
  setEditText: Dispatch<SetStateAction<string>>
  editBusy: boolean
  deleteCommentBusyId: number | null
  onStartEditComment: (comment: MovieCardComment) => void
  onCancelEditComment: () => void
  onSaveEditComment: (commentId: number, imageUrl: string | null) => Promise<void>
  onDeleteComment: (commentId: number) => void
  tasteQuizKnowledgeByAuthor: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  watchingByUserId: Record<string, WatchingNowBatchItem>
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
  setCommentRef,
  commentTextAreaRef,
  commentMentionAnchorRef,
  commentMentionPopoverLayout,
  insertReactionIntoComment,
  toggleSpoilerInComment,
  insertMovieCardIntoComment,
  commentDraftInlineCardRefs,
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
  commentImageUrl,
  setCommentImageUrl,
  commentImageUploadBusy,
  commentImageFileInputRef,
  handlePickCommentImage,
  handleCommentImageFileChange,
  editingCommentId,
  editText,
  setEditText,
  editBusy,
  deleteCommentBusyId,
  onStartEditComment,
  onCancelEditComment,
  onSaveEditComment,
  onDeleteComment,
  tasteQuizKnowledgeByAuthor,
  streakByUserId,
  watchingByUserId,
}: MovieCardDetailLoadedBodyProps) {
  const auth = useAuthStatus()
  const [cardAttachedAudio, setCardAttachedAudio] = useState<HTMLAudioElement | null>(null)
  const onCardAttachedAudio = useCallback((el: HTMLAudioElement | null) => {
    setCardAttachedAudio(el)
  }, [])
  const { openCompose } = useComposeFeedPost()
  const navigate = useNavigate()
  const location = useLocation()
  const primaryTitle = movieCardPrimaryTitle(card)
  const primaryPoster = movieCardPrimaryPoster(card)
  const synopsisShort = movieCardPrimarySummary(card)
  const showKinopoiskLink = movieCardHasKinopoiskLink(card)
  const fromFeed =
    typeof location.state === 'object' &&
    location.state !== null &&
    'fromFeed' in location.state &&
    Boolean((location.state as { fromFeed?: boolean }).fromFeed)
  const detailCardAuthor = movieCardAuthorOrNull(card)
  const oscarBadge = useMemo(
    () => primaryFilmAwardBadge(card.award_badges),
    [card.award_badges],
  )
  const watchNoteText = movieCardWatchNotePlainText(card)
  const showWatchNote = watchNoteText.trim().length > 0
  const isPlannedCard = card.is_planned === true
  const cardOverlapAnchor = useMemo(() => watchlistOverlapAnchorFromMovieCard(card), [card])
  const showCardRating = hasMeaningfulCardRating(card)
  const hasCardAudio = card.audio_url != null && card.audio_url.trim() !== ''
  const cardAudioUrlTrimmed = (card.audio_url ?? '').trim()

  const filmIdForCollections =
    card.film_id != null && card.film_id > 0 ? card.film_id : null
  const filmIdForWatch =
    filmIdForCollections != null && showKinopoiskLink ? filmIdForCollections : null
  const filmIdForFollowingCommunity =
    filmIdForWatch ?? (card.film_id != null && card.film_id > 0 ? card.film_id : null)
  const filmCollectionsQuery = useQuery<CollectionSummary[], Error>({
    queryKey: filmCollectionsQueryKey(filmIdForCollections ?? 0),
    queryFn: async () => {
      const data = await getFilmCollections(filmIdForCollections as number)
      return data.items
    },
    enabled: auth.kind === 'ready' && filmIdForCollections != null,
    staleTime: 60_000,
  })
  const filmCollectionsItems: CollectionSummary[] | null =
    filmIdForCollections == null
      ? []
      : filmCollectionsQuery.isError
        ? []
        : (filmCollectionsQuery.data ?? null)

  const filmPassportQuery = useQuery({
    queryKey: ['film-passport', filmIdForCollections],
    queryFn: () => getFilmById(filmIdForCollections as number),
    enabled: auth.kind === 'ready' && filmIdForCollections != null,
    staleTime: 300_000,
  })
  const filmPassport = filmPassportQuery.data ?? null

  const posterFs = useFullscreenImageActivator({
    enabled: Boolean(primaryPoster),
    imageSrc: primaryPoster ?? '',
    imageAlt: primaryTitle,
    onSingleNavigate: null,
  })

  return (
    <>
      <div className="space-y-3">
            <div className="filmony-card-detail-panel-enter group/poster overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] shadow-[inset_0_1px_0_rgba(255,255,255,0.045)] contain-[paint]">
              {isPlannedCard ? (
                <div className="flex flex-wrap items-center gap-2 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_55%,transparent)] px-3.5 py-2 sm:px-4">
                  <PlannedCardBadge variant="ribbon" />
                </div>
              ) : null}
              <div className="relative w-full overflow-hidden bg-(--tgui--bg_color)">
                <div
                  {...posterFs.bindings}
                  aria-hidden
                  tabIndex={-1}
                  className="relative isolate w-full outline-none!"
                >
                {primaryPoster ? (
                  <img
                    src={primaryPoster}
                    alt={primaryTitle}
                    className="filmony-detail-poster-img pointer-events-none relative z-0 block h-auto w-full max-w-none bg-(--tgui--divider_color) motion-safe:transition-transform motion-safe:duration-1100 motion-safe:ease-out motion-safe:group-hover/poster:scale-[1.02] motion-safe:origin-top"
                  />
                ) : (
                  <div className="flex min-h-40 w-full items-center justify-center px-4 py-12 text-sm text-(--tgui--hint_color)">
                    Нет постера
                  </div>
                )}
                <div
                  className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-linear-to-t from-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] via-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_35%,transparent)] to-transparent"
                  aria-hidden
                />
                {showCardRating ? (
                  <div className="pointer-events-none absolute left-2.5 top-2.5 z-10 sm:left-3.5 sm:top-3.5">
                    <div className="relative flex h-21 w-21 items-center justify-center sm:h-21.5 sm:w-21.5">
                      {hasCardAudio ? (
                        <MovieCardRatingAudioVisualizer
                          audio={cardAttachedAudio}
                          audioUrl={cardAudioUrlTrimmed}
                          ringColor={palette.ring}
                          compact
                        />
                      ) : null}
                      <div
                        className="filmony-detail-rating-ring relative z-10 flex h-14.5 w-14.5 shrink-0 flex-col items-center justify-center gap-px rounded-full border-2 bg-[color-mix(in_srgb,var(--filmony-void,#0a1018)_88%,transparent)] shadow-[0_8px_18px_rgba(0,0,0,0.3)] backdrop-blur-sm sm:h-15 sm:w-15"
                        style={{
                          borderColor: palette.ring,
                          color: palette.text,
                        }}
                      >
                        <span className="text-[7px] font-semibold uppercase leading-none tracking-[0.12em] text-(--tgui--hint_color) sm:text-[7.5px]">
                          Оценка
                        </span>
                        <span className="text-[1.05rem] font-extrabold leading-none tabular-nums tracking-tight sm:text-[1.1rem]">
                          {formatRating(card.rating)}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : null}
                {isOwner && showCardRating ? (
                  <div className="pointer-events-none absolute left-[4.75rem] top-3 z-10 sm:left-[5.25rem] sm:top-3.5">
                    <ContrarianBadge
                      rating={card.rating}
                      communityAvgRating={card.community_avg_rating}
                      isContrarian={card.is_contrarian}
                    />
                  </div>
                ) : null}
                {hasCardAudio ? (
                  <div className="absolute bottom-3 right-3 z-10 sm:bottom-4 sm:right-4">
                    <div className="filmony-detail-poster-audio-pill pointer-events-auto flex flex-col items-stretch">
                      <MovieCardAudioPlayer
                        cardId={card.id}
                        variant="compact"
                        audioUrl={cardAudioUrlTrimmed}
                        onAttachedAudioElement={onCardAttachedAudio}
                        className="items-center"
                      />
                    </div>
                  </div>
                ) : null}
                </div>
                {posterFs.overlay}
              </div>
              <div className="px-3.5 pb-3 pt-4 sm:px-4">
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1 pr-1">
                    <Title level="2" weight="2" className="text-[1.15rem]! leading-snug! sm:text-[1.2rem]!">
                      {primaryTitle}
                    </Title>
                    {isPlannedCard ? (
                      <p className="mt-1 text-sm leading-snug text-(--tgui--hint_color)">
                        Ещё не посмотрел — в списке «Позже»
                      </p>
                    ) : null}
                    <div className="mt-2">
                      <WatchlistOverlapAnchorBanner
                        anchor={cardOverlapAnchor}
                        enabled={!showCardRating || isPlannedCard}
                        inViewerWatchlist={isPlannedCard && isOwner ? true : false}
                      />
                    </div>
                    <div className="mt-2 flex min-w-0 flex-wrap items-center gap-1.5">
                      {detailCardAuthor != null ? (
                        <>
                          <CardAuthorAvatarLink author={detailCardAuthor} />
                          <TasteQuizCommentAuthorBadge
                            knowledgeByAuthor={tasteQuizKnowledgeByAuthor}
                            authorId={detailCardAuthor.id}
                            viewerId={viewerId}
                          />
                          <RatingStreakAuthorBadge
                            streakByUserId={streakByUserId}
                            authorId={detailCardAuthor.id}
                          />
                          <WatchingNowAuthorBadge
                            watchingByUserId={watchingByUserId}
                            authorId={detailCardAuthor.id}
                          />
                        </>
                      ) : null}
                      <OscarReleaseYearLabel
                        label={movieCardReleasePrimaryLabel(card)}
                        badge={oscarBadge}
                        releaseYear={card.release_year ?? card.film_year}
                        variant="inline"
                      />
                      <CardCategoryChip category={card.category} />
                      {card.film_primary_director_kinopoisk_id != null &&
                      card.film_primary_director_name != null &&
                      card.film_primary_director_name.trim() !== '' ? (
                        <DirectorChip
                          kinopoiskId={card.film_primary_director_kinopoisk_id}
                          name={card.film_primary_director_name}
                          size="sm"
                          className="min-w-0 max-w-[min(100%,12rem)]"
                        />
                      ) : null}
                      {card.film_franchise_key != null &&
                      card.film_franchise_label != null &&
                      card.film_franchise_label.trim() !== '' ? (
                        <FranchiseChip
                          franchiseKey={card.film_franchise_key}
                          label={card.film_franchise_label}
                          size="sm"
                          className="min-w-0 max-w-[min(100%,12rem)]"
                        />
                      ) : null}
                    </div>
                    <FilmGenreChips genres={card.film_genres} size="sm" className="mt-1.5" />
                    {filmPassport ? (
                      <FilmCatalogMetadata
                        film={filmPassport}
                        size="sm"
                        variant="compact"
                        className="mt-1.5"
                      />
                    ) : null}
                    <FilmSynopsisBlock
                      shortDescription={synopsisShort}
                      description={card.film_description ?? null}
                      maxLines={2}
                      className="mt-2"
                    />
                  </div>
                  <div className="flex shrink-0 items-center gap-0.5 pt-0.5">
                    {filmPassport?.trailer_youtube_url ? (
                      <FilmTrailerIconButton trailerYoutubeUrl={filmPassport.trailer_youtube_url} />
                    ) : null}
                    {showKinopoiskLink ? (
                      <IconButton
                        type="button"
                        size="s"
                        mode="gray"
                        aria-label="Открыть страницу темы на Кинопоиске"
                        onClick={() => {
                          const url = kinopoiskTitleUrlFromCard(
                            card.film_kinopoisk_id,
                            card.provider,
                            card.external_id,
                          )
                          if (url != null) openExternalUrl(url)
                        }}
                      >
                        <span className="relative z-1 flex h-[18px] min-w-[18px] items-center justify-center rounded-[4px] bg-[#ff6600] px-[3px] text-[8px] font-black leading-none tracking-tight text-white">
                          КП
                        </span>
                      </IconButton>
                    ) : null}
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
                        aria-label="Взять за основу — создать свою карточку с этой же темой"
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

            {filmIdForWatch != null ? (
              <>
                <Link
                  to={`/films/${encodeURIComponent(String(filmIdForWatch))}/watch`}
                  className="filmony-card-detail-panel-enter block no-underline"
                  onClick={(event) => { void onWatchCtaClick(event, filmIdForWatch) }}
                >
                  <Button stretched>Смотреть</Button>
                </Link>
              </>
            ) : null}

            {!isPlannedCard ? (
              <FollowingRatingsPanel
                compact
                className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-1"
                rows={followingRatings}
                communityLink={
                  card.provider === 'rawg' && card.catalog_item_id != null && card.catalog_item_id > 0
                    ? {
                        to: `/catalog/${encodeURIComponent(String(card.catalog_item_id))}`,
                      }
                    : filmIdForFollowingCommunity != null
                      ? {
                          to: `/films/${encodeURIComponent(String(filmIdForFollowingCommunity))}`,
                          label: 'Все оценки →',
                        }
                      : null
                }
              />
            ) : null}

            <section className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-1 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Теги</p>
              <div className="mt-2.5 flex flex-wrap gap-2">
                <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,var(--filmony-surface,#111b27))] px-3 py-1.5 text-xs font-medium text-(--tgui--text_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] transition duration-200 motion-safe:active:scale-[0.97]">
                  {COMPANY_LABELS[card.company]}
                </span>
                {!isPlannedCard ? (
                  <>
                    <span className="rounded-full border border-[color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] bg-transparent px-3 py-1.5 text-xs font-medium text-(--tgui--text_color) transition duration-200 motion-safe:active:scale-[0.97]">
                      {MOOD_BEFORE_LABELS[card.mood_before]}
                    </span>
                    <span className="rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_32%,var(--filmony-elevated,#182433))] px-3 py-1.5 text-xs font-semibold text-(--filmony-ink,#06090d) shadow-[0_1px_0_rgba(255,255,255,0.12)] transition duration-200 motion-safe:active:scale-[0.97]">
                      {MOOD_AFTER_LABELS[card.mood_after]}
                    </span>
                  </>
                ) : null}
              </div>
              {!isPlannedCard ? (
                <>
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
                </>
              ) : null}
              {showWatchNote ? (
                <>
                  <p className="mt-3.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">Заметка к карточке</p>
                  <p className="mt-2 whitespace-pre-wrap wrap-break-word text-sm leading-relaxed text-(--tgui--text_color)">
                    <CommentBodyWithReactionTokens text={watchNoteText} />
                  </p>
                </>
              ) : null}
              {isPlannedCard ? (
                <PlannedWatchPartnersList
                  partners={card.planned_watch_partners ?? []}
                  className="mt-3.5"
                />
              ) : null}
              {isPlannedCard && isOwner ? (
                <Button
                  type="button"
                  size="m"
                  stretched
                  className="mt-4!"
                  onClick={() => {
                    void navigate(plannedCardRateHref(card))
                  }}
                >
                  Поставить оценку
                </Button>
              ) : null}
            </section>

            {filmIdForCollections != null ? (
              <FilmCollectionsStrip
                className="filmony-card-detail-panel-enter filmony-card-detail-panel-enter--delay-2 mt-3"
                items={filmCollectionsItems}
              />
            ) : null}

            <CommentThreadSection
              comments={comments}
              commentsById={commentsById}
              commentsLoading={commentsLoading}
              commentsError={commentsError}
              commentsNextCursor={commentsNextCursor}
              loadComments={loadComments}
              replyTo={replyTo}
              setReplyTo={setReplyTo}
              viewerId={viewerId}
              submitBusy={submitBusy}
              jumpBusy={jumpBusy}
              highlightCommentId={highlightCommentId}
              setCommentRef={setCommentRef}
              handleJumpToParent={handleJumpToParent}
              handleCreateComment={handleCreateComment}
              commentText={commentText}
              onCommentTextChange={onCommentTextChange}
              onCommentKeyDown={onCommentKeyDown}
              onCommentKeyUp={onCommentKeyUp}
              onCommentSelect={onCommentSelect}
              commentTextAreaRef={commentTextAreaRef}
              commentDraftInlineCardRefs={commentDraftInlineCardRefs}
              insertReactionIntoComment={insertReactionIntoComment}
              toggleSpoilerInComment={toggleSpoilerInComment}
              insertMovieCardIntoComment={insertMovieCardIntoComment}
              charsLeft={charsLeft}
              commentMentionAnchorRef={commentMentionAnchorRef}
              commentMentionPicker={commentMentionPicker}
              commentMentionHighlightIdx={commentMentionHighlightIdx}
              commentMentionFiltered={commentMentionFiltered}
              commentMentionPopoverLayout={commentMentionPopoverLayout}
              followingMentionItems={followingMentionItems}
              followingMentionQueryPending={followingMentionQueryPending}
              followingMentionQueryError={followingMentionQueryError}
              onPickCommentMention={onPickCommentMention}
              onDismissCommentMention={onDismissCommentMention}
              tasteQuizKnowledgeByAuthor={tasteQuizKnowledgeByAuthor}
              streakByUserId={streakByUserId}
              watchingByUserId={watchingByUserId}
              editingCommentId={editingCommentId}
              editText={editText}
              setEditText={setEditText}
              editBusy={editBusy}
              deleteCommentBusyId={deleteCommentBusyId}
              onStartEditComment={onStartEditComment}
              onCancelEditComment={onCancelEditComment}
              onSaveEditComment={(comment) => void onSaveEditComment(comment.id, comment.image_url ?? null)}
              onDeleteComment={onDeleteComment}
              setComments={setComments}
              reactionTargetKind="movie_card_comment"
              commentImageUrl={commentImageUrl}
              setCommentImageUrl={setCommentImageUrl}
              commentImageUploadBusy={commentImageUploadBusy}
              commentImageFileInputRef={commentImageFileInputRef}
              handlePickCommentImage={handlePickCommentImage}
              handleCommentImageFileChange={handleCommentImageFileChange}
              onPublishToFeed={(comment) => {
                const d = movieCardCommentDerivedFields(comment)
                const payload: OpenComposeFeedPostPayload = {
                  sourceCommentId: d.id,
                  referencedMovieCardId: card.id,
                  sourceCommentImageUrl: d.sourceCommentImageUrl,
                  sourceCommentPreviewAuthorLabel: commentAuthorLabel(comment.author),
                  sourceCommentPreviewText: d.text,
                  sourceCommentReferencedMovieCards: d.referenced_movie_cards ?? null,
                  sourceCommentReferencedMentions: d.referenced_mentions ?? null,
                }
                openCompose(payload)
              }}
            />
          </div>
    </>
  )
}
