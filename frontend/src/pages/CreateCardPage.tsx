import { Button } from '@telegram-apps/telegram-ui'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { isLikelyUrl } from '../api/catalogApi'
import { createMovieCard, getFilmById, getMovieCardById } from '../api/cardApi'
import {
  createMyCardCategory,
  getMyMovieCardTagStats,
  getMyPlannedCard,
  getMyProfile,
  getMyCardCategories,
} from '../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MovieCard,
  MyMovieCardTagStatItem,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { CatalogCandidatesList } from '../components/create/CatalogCandidatesList'
import { RatedCardScrollForm } from '../components/create/RatedCardScrollForm'
import {
  globalFeedQueryRootKey,
  myCardCategoriesQueryKey,
  myMovieCardTagStatsQueryKey,
  userMovieCardTagStatsQueryKey,
} from '../feed/feedQueryKeys'
import { useCatalogCandidates } from '../hooks/useCatalogCandidates'
import { useResolveCatalogUrl } from '../hooks/useResolveCatalogUrl'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { recordRecentCardView } from '../lib/recentCardViews'
import {
  readCachedMyMovieCardTagStats,
  writeCachedMyMovieCardTagStats,
} from '../lib/movieCardTagStatsStorage'
import {
  bindingDisplayCover,
  bindingDisplaySummary,
  bindingDisplayTitle,
  bindingFromCatalogCandidate,
  bindingFromResolveByUrl,
  bindingHasRatedDuplicate,
  cardsNewPathPreserveReturnTo,
  creationBindingFromMovieCard,
  createManualBinding,
  CREATE_CARD_TEXT_FIELD_CLASS,
  mapResolveError,
  MAX_CUSTOM_TAG_LEN,
  normalizeRating,
  plannedCardLookupParams,
  type CreationBinding,
} from '../lib/createCardBinding'
import {
  movieCardPrimaryPoster,
  movieCardPrimaryTitle,
  movieCardReleaseCompactSuffix,
} from '../lib/movieCardDisplay'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { MAX_WATCH_NOTE_LEN } from '../lib/watchNoteLimits'

type CreateScreen = 'search' | 'form'

function applyBindingFields(binding: CreationBinding): {
  title: string
  summary: string
  coverUrl: string | null
} {
  const summaryRaw = bindingDisplaySummary(binding)
  return {
    title: bindingDisplayTitle(binding),
    summary: summaryRaw ?? '',
    coverUrl: bindingDisplayCover(binding),
  }
}

export function CreateCardPage() {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const initialFilmId = searchParams.get('filmId')
  const fromCardQuery = searchParams.get('fromCard')
  const [fromCardPrefillDone, setFromCardPrefillDone] = useState(
    () => fromCardQuery == null || fromCardQuery === '',
  )

  const [screen, setScreen] = useState<CreateScreen>('search')
  const [smartQuery, setSmartQuery] = useState('')
  const [creationBinding, setCreationBinding] = useState<CreationBinding | null>(null)
  const [displayTitle, setDisplayTitle] = useState('')
  const [displaySummary, setDisplaySummary] = useState('')
  const [displayCoverUrl, setDisplayCoverUrl] = useState<string | null>(null)
  const [remixFromCard, setRemixFromCard] = useState(false)
  const [pickBusy, setPickBusy] = useState(false)
  const [bootstrapBusy, setBootstrapBusy] = useState(false)
  const [searchInlineError, setSearchInlineError] = useState<string | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)

  const [rating, setRating] = useState(7.5)
  const [company, setCompany] = useState<CardCompany>('alone')
  const [moodBefore, setMoodBefore] = useState<CardMoodBefore>('relax')
  const [moodAfter, setMoodAfter] = useState<CardMoodAfter>('enjoyed')
  const [customTags, setCustomTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [tagFieldError, setTagFieldError] = useState<string | null>(null)
  const [watchNote, setWatchNote] = useState('')
  const [selectedShelfId, setSelectedShelfId] = useState<number | null>(null)
  const [newShelfDraft, setNewShelfDraft] = useState('')
  const [shelfCreateExpanded, setShelfCreateExpanded] = useState(false)
  const [shelfError, setShelfError] = useState<string | null>(null)
  const [createShelfBusy, setCreateShelfBusy] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const fromCardBootstrapSeq = useRef(0)
  const resolveAppliedRef = useRef<string | null>(null)

  const urlLike = isLikelyUrl(smartQuery)
  const candidatesQuery = useCatalogCandidates(smartQuery, {
    enabled: auth.kind === 'ready' && fromCardPrefillDone && screen === 'search' && !urlLike,
  })
  const resolveQuery = useResolveCatalogUrl(smartQuery, {
    enabled: auth.kind === 'ready' && fromCardPrefillDone && screen === 'search' && urlLike,
  })

  const tagStatsQuery = useQuery({
    queryKey: myMovieCardTagStatsQueryKey(),
    queryFn: async () => {
      const res = await getMyMovieCardTagStats()
      writeCachedMyMovieCardTagStats(res)
      return res
    },
    enabled: auth.kind === 'ready',
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
    placeholderData: () => readCachedMyMovieCardTagStats() ?? undefined,
  })

  const shelvesQuery = useQuery({
    queryKey: myCardCategoriesQueryKey(),
    queryFn: getMyCardCategories,
    enabled: auth.kind === 'ready',
    staleTime: 60_000,
    gcTime: 30 * 60_000,
  })

  const myTagStats: MyMovieCardTagStatItem[] = useMemo(
    () => tagStatsQuery.data?.items ?? [],
    [tagStatsQuery.data],
  )

  const shelves = useMemo(
    () => (shelvesQuery.data?.items ?? []).map((row) => ({ id: row.id, name: row.name })),
    [shelvesQuery.data],
  )

  const duplicateInfo = useMemo(
    () => (creationBinding != null ? bindingHasRatedDuplicate(creationBinding) : { has: false, myCardId: null }),
    [creationBinding],
  )

  const enterFormWithBinding = useCallback(async (binding: CreationBinding, opts?: { remix?: boolean }) => {
    const fields = applyBindingFields(binding)
    setCreationBinding(binding)
    setDisplayTitle(fields.title)
    setDisplaySummary(fields.summary)
    setDisplayCoverUrl(fields.coverUrl)
    setRemixFromCard(opts?.remix === true)
    setSubmitError(null)
    setScreen('form')

    const params = plannedCardLookupParams(binding)
    if (params == null) return
    try {
      const planned = await getMyPlannedCard(params)
      setCompany(planned.company)
      setSelectedShelfId(planned.category_id)
      setWatchNote(planned.watch_note)
    } catch {
      // no planned card
    }
  }, [])

  const skipCatalogFilmIdBootstrap = useMemo(() => {
    const raw = fromCardQuery
    return raw != null && raw !== ''
  }, [fromCardQuery])

  useEffect(() => {
    if (skipCatalogFilmIdBootstrap) return
    if (initialFilmId == null || initialFilmId === '') return
    const filmId = Number(initialFilmId)
    if (!Number.isInteger(filmId) || filmId <= 0) return

    let alive = true
    void (async () => {
      setBootstrapBusy(true)
      setPageError(null)
      try {
        const item = await getFilmById(filmId)
        if (!alive) return
        await enterFormWithBinding({ kind: 'film', film: item })
      } catch (e) {
        if (!alive) return
        setPageError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить данные из каталога')
      } finally {
        if (alive) setBootstrapBusy(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [enterFormWithBinding, initialFilmId, skipCatalogFilmIdBootstrap])

  useEffect(() => {
    const returnToParam = searchParams.get('returnTo')
    const cleanCreatePath = cardsNewPathPreserveReturnTo(returnToParam)
    const raw = searchParams.get('fromCard')
    const rateIntent = searchParams.get('intent') === 'rate'

    if (raw == null || raw === '') {
      queueMicrotask(() => setFromCardPrefillDone(true))
      return
    }
    const cardId = Number(raw)
    if (!Number.isInteger(cardId) || cardId <= 0) {
      queueMicrotask(() => {
        setPageError('Некорректная ссылка на карточку-шаблон')
        setFromCardPrefillDone(true)
        void navigate(cleanCreatePath, { replace: true })
      })
      return
    }

    const seq = ++fromCardBootstrapSeq.current
    let alive = true
    void (async () => {
      setBootstrapBusy(true)
      setPageError(null)
      try {
        const [card, me] = await Promise.all([getMovieCardById(cardId), getMyProfile()])
        if (!alive || seq !== fromCardBootstrapSeq.current) return

        if (card.user_id != null && card.user_id === me.id && card.is_planned === true) {
          if (!rateIntent) {
            void navigate(`/cards/${cardId}`, { replace: true })
            return
          }
          const binding = await creationBindingFromMovieCard(card)
          if (!alive || seq !== fromCardBootstrapSeq.current) return
          if (binding == null) {
            setPageError('Не удалось подготовить карточку для оценки')
            void navigate(cleanCreatePath, { replace: true })
            return
          }
          setCompany(card.company)
          setSelectedShelfId(card.category?.id ?? null)
          setWatchNote(card.watch_note ?? '')
          await enterFormWithBinding(binding)
          void navigate(cleanCreatePath, { replace: true })
          return
        }

        if (card.user_id != null && card.user_id === me.id) {
          setPageError('Свою карточку нельзя взять за основу — отредактируйте её или создайте новую из каталога.')
          void navigate(cleanCreatePath, { replace: true })
          return
        }

        let binding: CreationBinding
        if (card.film_id != null && card.film_id > 0) {
          const item = await getFilmById(card.film_id)
          if (!alive || seq !== fromCardBootstrapSeq.current) return
          binding = { kind: 'film', film: item }
        } else if (card.catalog_item_id != null && card.catalog_item_id > 0 && card.provider === 'rawg') {
          binding = {
            kind: 'catalog_game',
            catalogItemId: card.catalog_item_id,
            display_title: movieCardPrimaryTitle(card),
            display_cover_url: movieCardPrimaryPoster(card),
            display_summary: card.display_summary ?? null,
            subtitle: movieCardReleaseCompactSuffix(card),
          }
        } else if (card.provider === 'youtube' && (card.external_id ?? '').trim() !== '') {
          const externalId = card.external_id!.trim()
          binding = {
            kind: 'youtube_video',
            externalId,
            sourceUrl: `https://www.youtube.com/watch?v=${externalId}`,
            display_title: movieCardPrimaryTitle(card),
            display_cover_url: movieCardPrimaryPoster(card),
            display_summary: card.display_summary ?? null,
            myCardId: null,
          }
        } else {
          binding = {
            kind: 'manual',
            display_title: movieCardPrimaryTitle(card),
            display_cover_url: movieCardPrimaryPoster(card),
            display_summary: card.display_summary ?? null,
          }
        }
        if (!alive || seq !== fromCardBootstrapSeq.current) return
        await enterFormWithBinding(binding, { remix: true })
        void navigate(cleanCreatePath, { replace: true })
      } catch (e) {
        if (!alive || seq !== fromCardBootstrapSeq.current) return
        setPageError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить карточку-шаблон')
        void navigate(cleanCreatePath, { replace: true })
      } finally {
        if (alive && seq === fromCardBootstrapSeq.current) {
          setBootstrapBusy(false)
          setFromCardPrefillDone(true)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [enterFormWithBinding, navigate, searchParams])

  useEffect(() => {
    if (!urlLike || screen !== 'search') return
    if (!resolveQuery.isSuccess || resolveQuery.data == null) return
    const trimmed = smartQuery.trim()
    if (resolveAppliedRef.current === trimmed) return
    resolveAppliedRef.current = trimmed
    void enterFormWithBinding(bindingFromResolveByUrl(resolveQuery.data))
  }, [enterFormWithBinding, resolveQuery.data, resolveQuery.isSuccess, screen, smartQuery, urlLike])

  useEffect(() => {
    if (!urlLike) {
      resolveAppliedRef.current = null
    }
  }, [urlLike])

  const handlePickCandidate = useCallback(
    async (candidate: Parameters<typeof bindingFromCatalogCandidate>[0]) => {
      setPickBusy(true)
      setSearchInlineError(null)
      try {
        const binding = await bindingFromCatalogCandidate(candidate)
        await enterFormWithBinding(binding)
      } catch (e) {
        setSearchInlineError(
          e instanceof ApiError
            ? mapResolveError(formatApiDetail(e.detail))
            : 'Не удалось подтянуть запись из каталога — попробуйте другой вариант или создайте вручную.',
        )
      } finally {
        setPickBusy(false)
      }
    },
    [enterFormWithBinding],
  )

  const handleManualCreate = useCallback(() => {
    const title = smartQuery.trim()
    void enterFormWithBinding(createManualBinding(title))
  }, [enterFormWithBinding, smartQuery])

  const submitNewShelf = useCallback(
    async (onPickShelf: (id: number) => void = setSelectedShelfId) => {
      const name = newShelfDraft.trim()
      if (name === '') {
        setShelfError('Введите название полки')
        return
      }
      setCreateShelfBusy(true)
      setShelfError(null)
      try {
        const row = await createMyCardCategory({ name })
        setNewShelfDraft('')
        onPickShelf(row.id)
        setShelfCreateExpanded(false)
        void queryClient.invalidateQueries({ queryKey: myCardCategoriesQueryKey() })
        safeHapticSuccess()
      } catch (e) {
        setShelfError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось создать полку')
      } finally {
        setCreateShelfBusy(false)
      }
    },
    [newShelfDraft, queryClient],
  )

  const addTag = useCallback(() => {
    const trimmed = tagInput.trim()
    if (trimmed === '') return
    if (trimmed.length > MAX_CUSTOM_TAG_LEN) {
      setTagFieldError(`Тег не длиннее ${MAX_CUSTOM_TAG_LEN} символов`)
      return
    }
    const lowered = trimmed.toLowerCase()
    if (customTags.some((tag) => tag.toLowerCase() === lowered)) {
      setTagInput('')
      return
    }
    if (customTags.length >= 5) {
      setTagFieldError('Можно добавить не больше 5 тегов')
      return
    }
    setCustomTags((prev) => [...prev, trimmed])
    setTagInput('')
    setTagFieldError(null)
  }, [customTags, tagInput])

  const addTagFromSuggestion = useCallback(
    (label: string) => {
      const trimmed = label.trim()
      if (trimmed === '' || trimmed.length > MAX_CUSTOM_TAG_LEN) return
      const lowered = trimmed.toLowerCase()
      if (customTags.some((tag) => tag.toLowerCase() === lowered)) return
      if (customTags.length >= 5) {
        setTagFieldError('Можно добавить не больше 5 тегов')
        return
      }
      setCustomTags((prev) => [...prev, trimmed])
      setTagInput('')
      setTagFieldError(null)
    },
    [customTags],
  )

  const removeTag = useCallback((tag: string) => {
    setCustomTags((prev) => prev.filter((item) => item !== tag))
  }, [])

  const handleSubmit = useCallback(async () => {
    if (creationBinding == null) {
      setSubmitError('Сначала выберите тему')
      return
    }
    const titleTrimmed = displayTitle.trim()
    if (titleTrimmed === '') {
      setSubmitError('Введите название')
      return
    }
    setSubmitLoading(true)
    setSubmitError(null)
    try {
      const watchNotePayload = watchNote.trim().slice(0, MAX_WATCH_NOTE_LEN)
      const ratingPayload = normalizeRating(rating)
      const shelfOpt =
        selectedShelfId != null && Number.isFinite(selectedShelfId) && selectedShelfId >= 1
          ? { category_id: selectedShelfId }
          : {}
      const coverOpt =
        displayCoverUrl != null && displayCoverUrl.trim() !== ''
          ? { display_cover_url: displayCoverUrl.trim() }
          : {}
      const summaryOpt =
        displaySummary.trim() !== '' ? { display_summary: displaySummary.trim() } : {}

      let newCard: MovieCard
      if (creationBinding.kind === 'film') {
        const f = creationBinding.film
        newCard = await createMovieCard({
          film_id: f.id,
          kinopoisk_id: f.kinopoisk_id,
          genres: f.genres ?? [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
          ...coverOpt,
        })
      } else if (creationBinding.kind === 'catalog_film') {
        const f = creationBinding.film
        newCard = await createMovieCard({
          catalog_item_id: creationBinding.catalogItemId,
          genres: f.genres ?? [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
          ...coverOpt,
          ...summaryOpt,
        })
      } else if (creationBinding.kind === 'catalog_game') {
        newCard = await createMovieCard({
          catalog_item_id: creationBinding.catalogItemId,
          display_title: titleTrimmed,
          ...coverOpt,
          ...summaryOpt,
          genres: [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
        })
      } else if (creationBinding.kind === 'youtube_video') {
        const yt = creationBinding
        newCard = await createMovieCard({
          provider: 'youtube',
          external_id: yt.externalId,
          display_title: titleTrimmed,
          ...coverOpt,
          ...summaryOpt,
          source_url: yt.sourceUrl,
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
        })
      } else {
        newCard = await createMovieCard({
          provider: 'no_provider',
          display_title: titleTrimmed,
          ...coverOpt,
          ...summaryOpt,
          genres: [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
        })
      }

      const bundleUid = readMyProfileBundleCache()?.profile.id
      if (bundleUid != null && bundleUid !== '') {
        void queryClient.invalidateQueries({ queryKey: userMovieCardTagStatsQueryKey(bundleUid) })
      }
      void queryClient.invalidateQueries({ queryKey: myMovieCardTagStatsQueryKey() })
      clearMyProfileBundleCache()
      safeHapticSuccess()
      void queryClient.invalidateQueries({ queryKey: globalFeedQueryRootKey })
      if (bundleUid != null && bundleUid !== '') {
        recordRecentCardView(bundleUid, {
          id: newCard.id,
          film_title: movieCardPrimaryTitle(newCard),
          film_poster_url: movieCardPrimaryPoster(newCard),
        })
      }

      const returnToFeed = searchParams.get('returnTo') === 'feed'
      if (returnToFeed) {
        void navigate('/', { replace: true, state: { restoreFeedScroll: true } })
      } else {
        void navigate(`/cards/${newCard.id}`, { replace: true })
      }
    } catch (e) {
      setSubmitError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось создать карточку')
    } finally {
      setSubmitLoading(false)
    }
  }, [
    company,
    creationBinding,
    customTags,
    displayCoverUrl,
    displaySummary,
    displayTitle,
    moodAfter,
    moodBefore,
    navigate,
    queryClient,
    rating,
    searchParams,
    selectedShelfId,
    watchNote,
  ])

  const goBack = useCallback(() => {
    if (screen === 'form') {
      setScreen('search')
      setSubmitError(null)
      return
    }
    void navigate('/')
  }, [navigate, screen])

  const resolveErrorMessage =
    resolveQuery.isError && urlLike
      ? mapResolveError(resolveQuery.error.message || 'Не удалось получить данные по ссылке')
      : null

  const searchBusy = bootstrapBusy || pickBusy || (urlLike && resolveQuery.isFetching)

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 pb-3 pt-3">
          <button
            type="button"
            onClick={goBack}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) active:opacity-70"
            aria-label="Назад"
          >
            ←
          </button>
          <div className="text-center">
            <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">
              Новая карточка
            </h1>
            {screen === 'form' && remixFromCard ? (
              <p className="text-xs text-(--tgui--hint_color)">По мотивам чужой карточки</p>
            ) : null}
          </div>
          <span className="w-10" />
        </div>
      </header>

      <main className="space-y-4 px-4 py-6">
        {pageError != null ? (
          <div className="rounded-2xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_10%,transparent)] px-3 py-2">
            <p className="text-sm text-(--tgui--destructive_text_color)">{pageError}</p>
          </div>
        ) : null}

        {!fromCardPrefillDone || bootstrapBusy ? (
          <p className="filmony-text-panel py-16 text-center text-sm text-(--tgui--hint_color)">
            Загружаем данные…
          </p>
        ) : null}

        {fromCardPrefillDone && !bootstrapBusy && screen === 'search' ? (
          <section className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            <div className="border-b border-(--tgui--divider_color) px-4 py-3">
              <h2 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">
                Название или ссылка
              </h2>
            </div>
            <div className="filmony-text-panel space-y-4 p-4">
              <p className="text-sm text-(--tgui--hint_color)">
                Введите название для поиска в каталогах или вставьте ссылку на страницу Кинопоиска или YouTube.
              </p>
              <input
                id="create-card-smart-field"
                type="search"
                autoComplete="off"
                enterKeyHint="search"
                placeholder="Название или https://…"
                value={smartQuery}
                onChange={(e) => {
                  setSmartQuery(e.currentTarget.value)
                  setSearchInlineError(null)
                }}
                className={CREATE_CARD_TEXT_FIELD_CLASS}
              />

              {urlLike ? (
                <p className="text-sm text-(--tgui--hint_color)">
                  {resolveQuery.isFetching ? 'Распознаём ссылку…' : 'Ссылка — откроем форму после распознавания'}
                </p>
              ) : smartQuery.trim().length > 0 && smartQuery.trim().length < 3 ? (
                <p className="text-xs text-(--tgui--hint_color)">Для поиска нужно не меньше 3 символов.</p>
              ) : null}

              {(searchInlineError ?? resolveErrorMessage) != null ? (
                <div className="rounded-xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_8%,transparent)] px-3 py-2.5">
                  <p className="text-sm text-(--tgui--destructive_text_color)">
                    {searchInlineError ?? resolveErrorMessage}
                  </p>
                </div>
              ) : null}

              {!urlLike ? (
                <CatalogCandidatesList
                  items={candidatesQuery.data?.items ?? []}
                  meta={candidatesQuery.data?.meta}
                  loading={candidatesQuery.isFetching && !searchBusy}
                  errorMessage={
                    candidatesQuery.isError
                      ? candidatesQuery.error.message || 'Не удалось выполнить поиск'
                      : null
                  }
                  pickBusy={searchBusy}
                  onPick={(candidate) => void handlePickCandidate(candidate)}
                />
              ) : null}

              {!urlLike &&
              candidatesQuery.isSuccess &&
              smartQuery.trim().length >= 3 &&
              (candidatesQuery.data?.items.length ?? 0) === 0 &&
              !candidatesQuery.isFetching ? (
                <p className="text-sm text-(--tgui--hint_color)">
                  Ничего не нашли — уточните запрос или создайте карточку вручную.
                </p>
              ) : null}

              <Button mode="gray" stretched type="button" disabled={searchBusy} onClick={handleManualCreate}>
                Создать вручную
              </Button>
            </div>
          </section>
        ) : null}

        {fromCardPrefillDone && !bootstrapBusy && screen === 'form' && creationBinding != null ? (
          <section className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            <div className="border-b border-(--tgui--divider_color) px-4 py-3">
              <h2 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">
                Карточка
              </h2>
            </div>
            <div className="p-4">
              <RatedCardScrollForm
                binding={creationBinding}
                remixFromCard={remixFromCard}
                duplicateMyCardId={duplicateInfo.has ? duplicateInfo.myCardId : null}
                title={displayTitle}
                onTitleChange={setDisplayTitle}
                summary={displaySummary}
                onSummaryChange={setDisplaySummary}
                coverUrl={displayCoverUrl}
                onCoverUrlChange={setDisplayCoverUrl}
                rating={rating}
                onRatingChange={setRating}
                company={company}
                onCompanyChange={setCompany}
                moodBefore={moodBefore}
                onMoodBeforeChange={setMoodBefore}
                moodAfter={moodAfter}
                onMoodAfterChange={setMoodAfter}
                selectedShelfId={selectedShelfId}
                onSelectedShelfIdChange={setSelectedShelfId}
                shelves={shelves}
                shelvesLoading={shelvesQuery.isLoading}
                shelvesError={shelvesQuery.isError}
                shelfCreateExpanded={shelfCreateExpanded}
                onShelfCreateExpandedChange={setShelfCreateExpanded}
                newShelfDraft={newShelfDraft}
                onNewShelfDraftChange={setNewShelfDraft}
                shelfError={shelfError}
                createShelfBusy={createShelfBusy}
                onCreateShelf={() => void submitNewShelf()}
                customTags={customTags}
                tagInput={tagInput}
                onTagInputChange={(v) => {
                  setTagInput(v)
                  setTagFieldError(null)
                }}
                tagFieldError={tagFieldError}
                onAddTag={addTag}
                onAddTagFromSuggestion={addTagFromSuggestion}
                onRemoveTag={removeTag}
                myTagStats={myTagStats}
                watchNote={watchNote}
                onWatchNoteChange={(v) => {
                  setWatchNote(v)
                  setSubmitError(null)
                }}
                submitError={submitError}
                submitLoading={submitLoading}
                onSubmit={() => void handleSubmit()}
                onBackToSearch={() => {
                  setScreen('search')
                  setSubmitError(null)
                }}
              />
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}
