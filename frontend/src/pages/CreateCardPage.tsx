import { Button, Title } from '@telegram-apps/telegram-ui'
import { Clapperboard, Gamepad2, PenLine } from 'lucide-react'
import { useInfiniteQuery, useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import type { CatalogSearchHit, CatalogSearchResponse } from '../api/catalogApi'
import {
  inferCatalogProviderFromUrl,
  resolveCatalogByProviderUrl,
  searchCatalog,
} from '../api/catalogApi'
import { createMovieCard, getFilmById, getMovieCardById, resolveFilmByKinopoiskUrl, shareMovieCardWithFollowers } from '../api/cardApi'
import {
  createMyCardCategory,
  getMyMovieCardTagStats,
  getMyProfile,
  getMyCardCategories,
  getUserSubscriptions,
  postMyWatchlistFilm,
} from '../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  Film,
  MovieCard,
  MyMovieCardTagStatItem,
  SubscriptionListItem,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { CommentDraftMultiline } from '../components/comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../components/comments/CommentReactionTokenPicker'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { ShareFollowersPicker } from '../components/share/ShareFollowersPicker'
import {
  globalFeedQueryRootKey,
  myCardCategoriesQueryKey,
  myMovieCardTagStatsQueryKey,
  userMovieCardTagStatsQueryKey,
} from '../feed/feedQueryKeys'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { recordRecentCardView } from '../lib/recentCardViews'
import {
  readCachedMyMovieCardTagStats,
  writeCachedMyMovieCardTagStats,
} from '../lib/movieCardTagStatsStorage'
import { movieCardPrimaryPoster, movieCardPrimaryTitle } from '../lib/movieCardDisplay'
import { insertSnippetAtCaret, reactionTokenFromId } from '../lib/commentReactionTokens'
import { normalizeCatalogSearchQuery } from '../lib/normalizeCatalogSearchQuery'
import { safeHapticSuccess } from '../lib/safeHaptic'

import './CreateCardPage.css'

const COMPANY_OPTIONS: Array<{ value: CardCompany; label: string }> = [
  { value: 'alone', label: 'Один' },
  { value: 'partner', label: 'С партнером' },
  { value: 'friends', label: 'С друзьями' },
  { value: 'family', label: 'С семьей' },
]

const MOOD_BEFORE_OPTIONS: Array<{ value: CardMoodBefore; label: string }> = [
  { value: 'relax', label: 'Хотел расслабиться' },
  { value: 'laugh', label: 'Хотел поржать' },
  { value: 'sad', label: 'Хотел погрустить' },
  { value: 'thrill', label: 'Хотел напряжения' },
]

const MOOD_AFTER_OPTIONS: Array<{ value: CardMoodAfter; label: string }> = [
  { value: 'laughed', label: 'Угарал' },
  { value: 'cried', label: 'Плакал' },
  { value: 'enjoyed', label: 'Кайфанул' },
  { value: 'tense', label: 'Был напряжен' },
  { value: 'wasted_time', label: 'Зря потратил время' },
]

const CHIP_COLORS = [
  'bg-[#3B82F633] text-[#60A5FA]',
  'bg-[#F9731633] text-[#FDBA74]',
  'bg-[#22C55E33] text-[#86EFAC]',
  'bg-[#A855F733] text-[#D8B4FE]',
  'bg-[#EC489933] text-[#F9A8D4]',
] as const

/** Дольше 450 ms — меньше промежуточных запросов при наборе; React Query отменяет in-flight через AbortSignal. */
const CATALOG_SEARCH_DEBOUNCE_MS = 800

type WizardStep = 1 | 2 | 3 | 4
const TOTAL_STEPS = 4
const STEP_TITLES: Record<WizardStep, string> = {
  1: 'Что добавляем',
  2: 'Проверьте тему',
  3: 'Оценка и полка',
  4: 'Детали и отправка',
}

/** Экран шага 1: источник темы (каталог или вручную) → поиск / ссылка. */
type CardAddKind = null | 'film' | 'game' | 'manual'

type CreationBinding =
  | { kind: 'film'; film: Film }
  | { kind: 'catalog_film'; catalogItemId: number; film: Film }
  | {
      kind: 'catalog_game'
      catalogItemId: number
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
      subtitle: string | null
    }
  | {
      kind: 'manual'
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
    }

/** Kinopoisk-backed каталог: id `Film` для legacy watchlist API. */
function watchlistKinopoiskFilmId(binding: CreationBinding): number | null {
  if (binding.kind === 'manual' || binding.kind === 'catalog_game') return null
  if (binding.kind === 'catalog_film') return binding.film.id
  return binding.film.id
}

async function hydrateKinopoiskCatalogFilm(externalId: string): Promise<Film> {
  const id = externalId.trim()
  try {
    return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/film/${id}/`)
  } catch (firstErr) {
    try {
      return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/series/${id}/`)
    } catch {
      throw firstErr
    }
  }
}

const WIZARD_TEXT_FIELD_CLASS =
  'w-full min-h-11 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none transition-[border-color,box-shadow] placeholder:text-(--tgui--hint_color) focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'

/** Совпадает с бэкендом `create_movie_card._normalize_tags`. */
const MAX_CUSTOM_TAG_LEN = 40
const MAX_WATCH_NOTE_LEN = 500

/** После мастера создания сохраняем returnTo=feed в URL при strip query-параметров. */
function cardsNewPathPreserveReturnTo(returnTo: string | null): string {
  return returnTo === 'feed' ? '/cards/new?returnTo=feed' : '/cards/new'
}

function kinopoiskCatalogRowHasMyCard(f: Film): boolean {
  return f.my_card_id != null && f.my_card_id > 0
}

function WizardStepPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="border-b border-(--tgui--divider_color) px-4 py-3">
        <h2 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function normalizeRating(value: number): number {
  const clamped = Math.max(1, Math.min(10, value))
  return Math.round(clamped * 2) / 2
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function mapResolveError(detail: string): string {
  const normalized = detail.toLowerCase()
  if (normalized.includes('empty url')) {
    return 'Вставьте ссылку на страницу записи каталога на Кинопоиске.'
  }
  if (normalized.includes('url must be from kinopoisk.ru')) {
    return 'Нужна ссылка с домена kinopoisk.ru.'
  }
  if (
    normalized.includes('kinopoisk id was not found in url') ||
    normalized.includes('film id was not found in url')
  ) {
    return 'Не получилось прочитать номер из ссылки. Скопируйте полный адрес страницы на Кинопоиске (из строки браузера).'
  }
  return detail
}

export function CreateCardPage() {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialFilmId = searchParams.get('filmId')
  const fromCardQuery = searchParams.get('fromCard')
  const [fromCardPrefillDone, setFromCardPrefillDone] = useState(() => fromCardQuery == null || fromCardQuery === '')
  const [remixFromCard, setRemixFromCard] = useState(false)
  const [step, setStep] = useState<WizardStep>(1)
  const [addKind, setAddKind] = useState<CardAddKind>(null)
  /** Поиск в каталоге: порог длины зависит от провайдера (Кинопоиск ≥3, RAWG ≥4), плюс debounce. */
  const [catalogSearchDraft, setCatalogSearchDraft] = useState('')
  const [debouncedCatalogSearch, setDebouncedCatalogSearch] = useState('')
  const [urlShortcutOpen, setUrlShortcutOpen] = useState(false)
  const [kinopoiskUrl, setKinopoiskUrl] = useState('')
  const [resolutionBusy, setResolutionBusy] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [watchlistBusy, setWatchlistBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resolveInlineError, setResolveInlineError] = useState<string | null>(null)
  const [manualFieldError, setManualFieldError] = useState<string | null>(null)
  const [shelfError, setShelfError] = useState<string | null>(null)
  const [shelfCreateExpanded, setShelfCreateExpanded] = useState(false)
  const [tagFieldError, setTagFieldError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [watchlistError, setWatchlistError] = useState<string | null>(null)
  const [creationBinding, setCreationBinding] = useState<CreationBinding | null>(null)
  const [manualTitle, setManualTitle] = useState('')
  const [manualCoverUrl, setManualCoverUrl] = useState('')
  const [manualSummary, setManualSummary] = useState('')
  const [rating, setRating] = useState(7.5)
  const [company, setCompany] = useState<CardCompany>('alone')
  const [moodBefore, setMoodBefore] = useState<CardMoodBefore>('relax')
  const [moodAfter, setMoodAfter] = useState<CardMoodAfter>('enjoyed')
  const [customTags, setCustomTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [watchNote, setWatchNote] = useState('')
  const [shareComment, setShareComment] = useState('')
  const [shareFollowers, setShareFollowers] = useState<SubscriptionListItem[]>([])
  const [shareFollowersLoading, setShareFollowersLoading] = useState(false)
  const [shareSelected, setShareSelected] = useState<Set<string>>(() => new Set())
  /** `null` — не передаём `category_id`, бэкенд подставляет полку по умолчанию. */
  const [selectedShelfId, setSelectedShelfId] = useState<number | null>(null)
  const [newShelfDraft, setNewShelfDraft] = useState('')
  const [createShelfBusy, setCreateShelfBusy] = useState(false)
  const fromCardBootstrapSeq = useRef(0)
  const watchNoteRef = useRef<HTMLTextAreaElement>(null)

  const insertReactionIntoWatchNote = useCallback(
    (id: number) => {
      const token = reactionTokenFromId(id)
      const el = watchNoteRef.current
      const inserted = insertSnippetAtCaret(
        watchNote,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        MAX_WATCH_NOTE_LEN,
      )
      if (!inserted) return
      setWatchNote(inserted.nextValue)
      window.requestAnimationFrame(() => {
        const target = watchNoteRef.current
        if (!target) return
        target.focus()
        target.setSelectionRange(inserted.caret, inserted.caret)
      })
    },
    [watchNote],
  )

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

  const catalogSearchNormalized = useMemo(
    () => normalizeCatalogSearchQuery(catalogSearchDraft),
    [catalogSearchDraft],
  )

  useEffect(() => {
    if (addKind !== 'film' && addKind !== 'game') {
      return
    }
    const minLen = addKind === 'game' ? 4 : 3
    if (catalogSearchNormalized.length < minLen) {
      const t = window.setTimeout(() => setDebouncedCatalogSearch(''))
      return () => window.clearTimeout(t)
    }
    const t = window.setTimeout(() => setDebouncedCatalogSearch(catalogSearchNormalized), CATALOG_SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }, [addKind, catalogSearchNormalized])

  useEffect(() => {
    queueMicrotask(() => {
      setCatalogSearchDraft('')
      setDebouncedCatalogSearch('')
      setUrlShortcutOpen(false)
    })
  }, [addKind])

  const catalogSearchProvider = addKind === 'film' ? 'kinopoisk' : addKind === 'game' ? 'rawg' : null

  const catalogSearchMinLen = catalogSearchProvider === 'rawg' ? 4 : 3

  type CatalogSearchQueryKey = readonly ['catalogSearch', 'kinopoisk' | 'rawg' | 'idle', string]

  const catalogSearchQueryKey: CatalogSearchQueryKey = [
    'catalogSearch',
    catalogSearchProvider ?? 'idle',
    debouncedCatalogSearch,
  ]

  const catalogSearchQuery = useInfiniteQuery<
    CatalogSearchResponse,
    Error,
    InfiniteData<CatalogSearchResponse>,
    CatalogSearchQueryKey,
    number
  >({
    queryKey: catalogSearchQueryKey,
    queryFn: ({ pageParam, signal }: { pageParam: number; signal: AbortSignal }) =>
      searchCatalog({
        provider: catalogSearchProvider!,
        q: debouncedCatalogSearch,
        page: pageParam,
        limit: 15,
        signal,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, _pages, lastPageParam): number | undefined => {
      if (!lastPage.has_more) return undefined
      const prev = typeof lastPageParam === 'number' ? lastPageParam : 1
      return prev + 1
    },
    enabled:
      auth.kind === 'ready' &&
      fromCardPrefillDone &&
      step === 1 &&
      catalogSearchProvider != null &&
      debouncedCatalogSearch.length >= catalogSearchMinLen,
  })

  const catalogSearchHits: CatalogSearchHit[] = useMemo(() => {
    const raw = catalogSearchQuery.data?.pages
    if (raw == null) return []
    const out: CatalogSearchHit[] = []
    for (const page of raw) {
      const items = page.items
      out.push(...items)
    }
    return out
  }, [catalogSearchQuery.data])

  const myTagStats: MyMovieCardTagStatItem[] = useMemo(
    () => tagStatsQuery.data?.items ?? [],
    [tagStatsQuery.data],
  )

  const skipCatalogFilmIdBootstrap = useMemo(() => {
    const raw = fromCardQuery
    return raw != null && raw !== ''
  }, [fromCardQuery])

  useEffect(() => {
    if (skipCatalogFilmIdBootstrap) {
      return
    }
    if (initialFilmId == null || initialFilmId === '') {
      return
    }
    const filmId = Number(initialFilmId)
    if (!Number.isInteger(filmId) || filmId <= 0) {
      return
    }
    void (async () => {
      setResolutionBusy(true)
      try {
        const item = await getFilmById(filmId)
        setCreationBinding({ kind: 'film', film: item })
        setStep(2)
      } catch (e) {
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить данные из каталога')
        }
      } finally {
        setResolutionBusy(false)
      }
    })()
  }, [initialFilmId, skipCatalogFilmIdBootstrap])

  useEffect(() => {
    const returnToParam = searchParams.get('returnTo')
    const cleanCreatePath = cardsNewPathPreserveReturnTo(returnToParam)

    const raw = searchParams.get('fromCard')
    if (raw == null || raw === '') {
      queueMicrotask(() => {
        setFromCardPrefillDone(true)
      })
      return
    }
    const cardId = Number(raw)
    if (!Number.isInteger(cardId) || cardId <= 0) {
      queueMicrotask(() => {
        setError('Некорректная ссылка на карточку-шаблон')
        setFromCardPrefillDone(true)
        void navigate(cleanCreatePath, { replace: true })
      })
      return
    }

    const seq = ++fromCardBootstrapSeq.current
    let alive = true
    void (async () => {
      setResolutionBusy(true)
      setError(null)
      try {
        const [card, me] = await Promise.all([getMovieCardById(cardId), getMyProfile()])
        if (!alive || seq !== fromCardBootstrapSeq.current) return
        if (card.user_id != null && card.user_id === me.id) {
          setError('Свою карточку нельзя взять за основу — отредактируйте её или создайте новую из каталога по ссылке.')
          void navigate(cleanCreatePath, { replace: true })
          return
        }
        if (card.film_id != null && card.film_id > 0) {
          const item = await getFilmById(card.film_id)
          if (!alive || seq !== fromCardBootstrapSeq.current) return
          setCreationBinding({ kind: 'film', film: item })
        } else {
          if (!alive || seq !== fromCardBootstrapSeq.current) return
          setCreationBinding({
            kind: 'manual',
            display_title: movieCardPrimaryTitle(card),
            display_cover_url: movieCardPrimaryPoster(card),
            display_summary: card.display_summary ?? null,
          })
        }
        setRemixFromCard(true)
        setStep(2)
        void navigate(cleanCreatePath, { replace: true })
      } catch (e) {
        if (!alive || seq !== fromCardBootstrapSeq.current) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить карточку-шаблон')
        }
        void navigate(cleanCreatePath, { replace: true })
      } finally {
        setResolutionBusy(false)
        if (alive && seq === fromCardBootstrapSeq.current) {
          setFromCardPrefillDone(true)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [navigate, searchParams])

  useEffect(() => {
    if (step !== 4 || auth.kind !== 'ready') {
      return
    }
    let alive = true
    void (async () => {
      setShareFollowersLoading(true)
      try {
        const me = await getMyProfile()
        if (!alive) return
        const subs = await getUserSubscriptions(me.id, 'followers')
        if (!alive) return
        setShareFollowers(subs.items.filter((x) => x.relation_type === 'follower'))
      } catch {
        if (!alive) return
        setShareFollowers([])
      } finally {
        if (alive) setShareFollowersLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [step, auth.kind])

  const customTagsLower = useMemo(() => new Set(customTags.map((t) => t.toLowerCase())), [customTags])

  const popularTagSuggestions = useMemo(() => {
    const out: MyMovieCardTagStatItem[] = []
    for (const row of myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      out.push(row)
      if (out.length >= 14) break
    }
    return out
  }, [myTagStats, customTagsLower])

  const inputPrefixSuggestions = useMemo(() => {
    const raw = tagInput.trim()
    if (raw === '') return []
    const p = raw.toLowerCase()
    const out: MyMovieCardTagStatItem[] = []
    for (const row of myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      if (!row.tag.toLowerCase().startsWith(p)) continue
      out.push(row)
      if (out.length >= 24) break
    }
    return out
  }, [tagInput, myTagStats, customTagsLower])

  const tagInputTooLong = tagInput.trim().length > MAX_CUSTOM_TAG_LEN
  const watchNoteTooLong = watchNote.length > MAX_WATCH_NOTE_LEN
  const canSubmitFinal = !tagInputTooLong && !watchNoteTooLong && creationBinding != null

  const confirmPreview = useMemo(() => {
    const b = creationBinding
    if (b == null) return null
    if (b.kind === 'manual') {
      return {
        posterUrl: b.display_cover_url,
        title: b.display_title,
        yearLabel: '—',
        genres: [] as string[],
        showDupWarning: false,
        myCardId: null as number | null,
        showWatchlist: false,
      }
    }
    if (b.kind === 'catalog_game') {
      const sub = (b.subtitle ?? '').trim()
      return {
        posterUrl: b.display_cover_url,
        title: b.display_title,
        yearLabel: sub !== '' ? sub : 'Каталог RAWG',
        genres: [] as string[],
        showDupWarning: false,
        myCardId: null as number | null,
        showWatchlist: false,
      }
    }
    const f = b.film
    return {
      posterUrl: f.poster_url ?? null,
      title: f.title,
      yearLabel: f.year != null ? String(f.year) : 'Год неизвестен',
      genres: f.genres ?? [],
      showDupWarning: kinopoiskCatalogRowHasMyCard(f),
      myCardId: f.my_card_id ?? null,
      showWatchlist: true,
    }
  }, [creationBinding])

  const sharePreview = confirmPreview

  function toggleShareRecipient(userId: string) {
    setShareSelected((prev) => {
      const next = new Set(prev)
      if (next.has(userId)) next.delete(userId)
      else next.add(userId)
      return next
    })
  }

  async function handleSelectKinopoiskSearchHit(hit: CatalogSearchHit) {
    if (hit.catalog_item_id == null || hit.kind !== 'film') {
      setResolveInlineError('У результата нет привязки к каталогу — попробуйте другой вариант или введите ссылку.')
      return
    }
    setResolutionBusy(true)
    setResolveInlineError(null)
    try {
      const catalogFilm = await hydrateKinopoiskCatalogFilm(hit.external_id)
      setCreationBinding({
        kind: 'catalog_film',
        catalogItemId: hit.catalog_item_id,
        film: catalogFilm,
      })
      setStep(2)
    } catch (e) {
      if (e instanceof ApiError) {
        setResolveInlineError(mapResolveError(formatApiDetail(e.detail)))
      } else {
        setResolveInlineError('Не удалось подтянуть запись из каталога — попробуйте ссылку на Кинопоиск.')
      }
    } finally {
      setResolutionBusy(false)
    }
  }

  function handleSelectRawgSearchHit(hit: CatalogSearchHit) {
    if (hit.catalog_item_id == null || hit.kind !== 'game') {
      setResolveInlineError('У результата нет привязки к каталогу — попробуйте другой вариант или создайте карточку вручную.')
      return
    }
    const title = hit.title.trim()
    if (title === '') {
      setResolveInlineError('У записи пустое название.')
      return
    }
    setResolveInlineError(null)
    setCreationBinding({
      kind: 'catalog_game',
      catalogItemId: hit.catalog_item_id,
      display_title: title,
      display_cover_url: hit.cover_url,
      display_summary: null,
      subtitle: hit.subtitle,
    })
    setStep(2)
  }

  async function handleResolveCatalogUrl() {
    if (kinopoiskUrl.trim() === '') {
      setResolveInlineError('Вставьте ссылку на страницу в поддерживаемом каталоге (например Кинопоиск).')
      return
    }
    const trimmedUrl = kinopoiskUrl.trim()
    setResolutionBusy(true)
    setResolveInlineError(null)
    try {
      const provider = inferCatalogProviderFromUrl(trimmedUrl)
      if (provider != null) {
        try {
          const resolved = await resolveCatalogByProviderUrl(provider, trimmedUrl)
          setCreationBinding({
            kind: 'catalog_film',
            catalogItemId: resolved.catalog_item_id,
            film: resolved.film,
          })
          setStep(2)
          return
        } catch (e) {
          const fallback =
            e instanceof ApiError && (e.status === 422 || e.status === 404 || e.status === 501)
          if (!fallback) throw e
        }
      }
      const item = await resolveFilmByKinopoiskUrl(trimmedUrl)
      setCreationBinding({ kind: 'film', film: item })
      setStep(2)
    } catch (e) {
      if (e instanceof ApiError) {
        setResolveInlineError(mapResolveError(formatApiDetail(e.detail)))
      } else {
        setResolveInlineError('Не удалось получить данные по ссылке. Проверьте адрес или создайте карточку вручную.')
      }
    } finally {
      setResolutionBusy(false)
    }
  }

  function handleManualContinue() {
    const title = manualTitle.trim()
    if (title === '') {
      setManualFieldError('Введите название темы')
      return
    }
    setManualFieldError(null)
    setResolveInlineError(null)
    const cover = manualCoverUrl.trim()
    const sum = manualSummary.trim()
    setCreationBinding({
      kind: 'manual',
      display_title: title,
      display_cover_url: cover === '' ? null : cover,
      display_summary: sum === '' ? null : sum,
    })
    setStep(2)
  }

  async function submitNewShelf() {
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
      setSelectedShelfId(row.id)
      setShelfCreateExpanded(false)
      void queryClient.invalidateQueries({ queryKey: myCardCategoriesQueryKey() })
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setShelfError(formatApiDetail(e.detail))
      } else {
        setShelfError('Не удалось создать полку')
      }
    } finally {
      setCreateShelfBusy(false)
    }
  }

  async function handleAddToWatchlist() {
    if (creationBinding == null || creationBinding.kind === 'manual') {
      return
    }
    const fid = watchlistKinopoiskFilmId(creationBinding)
    if (fid == null || fid <= 0) {
      return
    }
    setWatchlistBusy(true)
    setWatchlistError(null)
    try {
      await postMyWatchlistFilm(fid)
      clearMyProfileBundleCache()
      safeHapticSuccess()
      void navigate('/profile', { replace: true, state: { moviesSegment: 'watchlist' as const } })
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          setWatchlistError('Эта тема уже в списке «Позже».')
          return
        }
        const msg = formatApiDetail(e.detail).toLowerCase()
        if (msg.includes('movie card already exists')) {
          setWatchlistError('У вас уже есть оценённая карточка для этой темы.')
          return
        }
        setWatchlistError(formatApiDetail(e.detail))
      } else {
        setWatchlistError('Не удалось добавить в список')
      }
    } finally {
      setWatchlistBusy(false)
    }
  }

  function addTag() {
    const trimmed = tagInput.trim()
    if (trimmed === '') {
      return
    }
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
  }

  function addTagFromSuggestion(label: string) {
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
  }

  function removeTag(tag: string) {
    setCustomTags((prev) => prev.filter((item) => item !== tag))
  }

  function goBack() {
    if (step === 1) {
      if (addKind != null) {
        setAddKind(null)
        setResolveInlineError(null)
        setManualFieldError(null)
        setKinopoiskUrl('')
        return
      }
      void navigate('/')
      return
    }
    setError(null)
    setSubmitError(null)
    setStep((prev) => {
      const next = (prev - 1) as WizardStep
      if (next === 1) {
        setCreationBinding(null)
        setAddKind(null)
        setResolveInlineError(null)
        setManualFieldError(null)
        setKinopoiskUrl('')
      }
      return next
    })
  }

  function renderChoiceChips<T extends string>(
    options: Array<{ value: T; label: string }>,
    selected: T,
    onSelect: (value: T) => void
  ) {
    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map((option, index) => {
          const isSelected = option.value === selected
          const color = CHIP_COLORS[index % CHIP_COLORS.length]
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onSelect(option.value)}
              className={`rounded-xl border px-3 py-2 text-xs font-medium transition active:scale-[0.99] ${
                isSelected
                  ? 'border-(--tgui--link_color) ring-1 ring-(--tgui--link_color) shadow-[0_0_0_1px_color-mix(in_srgb,var(--tgui--link_color)_20%,transparent)]'
                  : 'border-(--tgui--divider_color) opacity-90'
              } ${color}`}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    )
  }

  async function handleSubmit() {
    if (creationBinding == null) {
      setSubmitError('Сначала выберите тему или источник')
      return
    }
    if (!canSubmitFinal) {
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
        })
      } else if (creationBinding.kind === 'catalog_game') {
        const g = creationBinding
        newCard = await createMovieCard({
          catalog_item_id: g.catalogItemId,
          display_title: g.display_title.trim(),
          display_cover_url: g.display_cover_url ?? undefined,
          display_summary: g.display_summary ?? undefined,
          genres: [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
          ...shelfOpt,
        })
      } else {
        const m = creationBinding
        newCard = await createMovieCard({
          provider: 'no_provider',
          display_title: m.display_title.trim(),
          display_cover_url: m.display_cover_url ?? undefined,
          display_summary: m.display_summary ?? undefined,
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
      if (shareSelected.size > 0) {
        try {
          await shareMovieCardWithFollowers(newCard.id, [...shareSelected], {
            shareComment: shareComment.trim().slice(0, MAX_WATCH_NOTE_LEN),
          })
        } catch {
          void navigate(`/cards/${newCard.id}/share`)
          return
        }
      }
      if (returnToFeed) {
        void navigate('/', { replace: true, state: { restoreFeedScroll: true } })
      } else {
        void navigate('/profile')
      }
    } catch (e) {
      if (e instanceof ApiError) {
        setSubmitError(formatApiDetail(e.detail))
      } else {
        setSubmitError('Не удалось создать карточку')
      }
    } finally {
      setSubmitLoading(false)
    }
  }

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 pb-2 pt-3">
          <button
            type="button"
            onClick={goBack}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) active:opacity-70"
            aria-label="Назад"
          >
            ←
          </button>
          <div className="text-center">
            <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">Новая карточка</h1>
            <p className="text-xs text-(--tgui--hint_color)">
              {remixFromCard ? 'По мотивам чужой карточки · ' : null}
              Шаг {step} из {TOTAL_STEPS}: {STEP_TITLES[step]}
            </p>
          </div>
          <span className="w-10" />
        </div>
        <div className="px-4 pb-3">
          <div className="h-1.5 overflow-hidden rounded-full bg-(--tgui--secondary_bg_color)">
            <div
              className="h-full rounded-full bg-(--tgui--link_color) transition-all duration-300"
              style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
            />
          </div>
        </div>
      </header>

      <main className="space-y-4 px-4 py-6">
        {error != null ? (
          <div className="rounded-2xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_10%,transparent)] px-3 py-2">
            <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p>
          </div>
        ) : null}

        {!fromCardPrefillDone ? (
          <p className="filmony-text-panel py-16 text-center text-sm text-(--tgui--hint_color)">
            Загружаем данные из карточки…
          </p>
        ) : null}

        {fromCardPrefillDone && step === 1 ? (
          <WizardStepPanel title="1. Что добавляем?">
            <div className="filmony-text-panel flex flex-col gap-4">
              {addKind === null ? (
                <>
                  <p className="create-card-source-lead text-sm text-(--tgui--text_color)">
                    Выберите тип темы
                  </p>
                  <div className="create-card-source-stack">
                    <button
                      type="button"
                      className="create-card-source-option create-card-source-option-primary"
                      aria-label="Фильм или сериал: поиск по каталогу Кинопоиска для фильмов и сериалов"
                      onClick={() => {
                        setAddKind('film')
                        setResolveInlineError(null)
                      }}
                    >
                      <span className="create-card-source-option-icon" aria-hidden="true">
                        <Clapperboard className="block" size={22} strokeWidth={1.75} />
                      </span>
                      <span className="create-card-source-option-text">
                        <span className="create-card-source-option-title">Фильм или сериал</span>
                      </span>
                    </button>
                    <button
                      type="button"
                      className="create-card-source-option"
                      aria-label="Игра: поиск в каталоге RAWG"
                      onClick={() => {
                        setAddKind('game')
                        setResolveInlineError(null)
                      }}
                    >
                      <span className="create-card-source-option-icon" aria-hidden="true">
                        <Gamepad2 className="block" size={22} strokeWidth={1.75} />
                      </span>
                      <span className="create-card-source-option-text">
                        <span className="create-card-source-option-title">Игра</span>
                      </span>
                    </button>
                    <button
                      type="button"
                      className="create-card-source-option"
                      aria-label="Вручную: своё название и обложка, если темы нет в каталогах"
                      onClick={() => {
                        setAddKind('manual')
                        setManualFieldError(null)
                        setResolveInlineError(null)
                      }}
                    >
                      <span className="create-card-source-option-icon" aria-hidden="true">
                        <PenLine className="block" size={22} strokeWidth={1.75} />
                      </span>
                      <span className="create-card-source-option-text">
                        <span className="create-card-source-option-title">Вручную</span>
                      </span>
                    </button>
                  </div>
                </>
              ) : null}

              {addKind === 'film' || addKind === 'game' ? (
                <>
                  <button
                    type="button"
                    className="self-start text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                    onClick={() => {
                      setAddKind(null)
                      setResolveInlineError(null)
                      setKinopoiskUrl('')
                      setUrlShortcutOpen(false)
                    }}
                  >
                    ← Другой тип
                  </button>
                  <div
                    className="create-card-source-reveal"
                    role="region"
                    aria-label={addKind === 'film' ? 'Поиск фильма или сериала' : 'Поиск игры'}
                  >
                    {addKind === 'film' ? (
                      <>
                        <p className="create-card-source-reveal-title">Кинопоиск</p>
                        <p className="create-card-source-reveal-body">
                          Поиск по названию (от 3 символов). Ниже также можно открыть ввод по ссылке на страницу
                          на Кинопоиске.
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="create-card-source-reveal-title">RAWG</p>
                        <p className="create-card-source-reveal-body">
                          Большая база игр с обложками. Для поиска нужно не меньше 4 символов. Если записи нет — можно
                          перейти к ручному вводу.
                        </p>
                      </>
                    )}
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label
                      htmlFor="create-card-catalog-search"
                      className="text-xs font-medium text-(--tgui--hint_color)"
                    >
                      {addKind === 'film' ? 'Название фильма или сериала' : 'Название игры'}
                    </label>
                    <input
                      id="create-card-catalog-search"
                      type="search"
                      autoComplete="off"
                      enterKeyHint="search"
                      placeholder={addKind === 'game' ? 'Минимум 4 символа…' : 'Минимум 3 символа…'}
                      value={catalogSearchDraft}
                      onChange={(e) => {
                        setCatalogSearchDraft(e.currentTarget.value)
                        setResolveInlineError(null)
                      }}
                      className={WIZARD_TEXT_FIELD_CLASS}
                    />
                  </div>
                  {catalogSearchNormalized.length > 0 && catalogSearchNormalized.length < catalogSearchMinLen ? (
                    <p className="text-xs text-(--tgui--hint_color)">
                      {catalogSearchMinLen === 4
                        ? 'Для поиска в RAWG введите не меньше 4 символов.'
                        : 'Для запроса в Кинопоиске нужно не меньше 3 символов.'}
                    </p>
                  ) : null}
                  {catalogSearchQuery.isFetching && debouncedCatalogSearch.length >= catalogSearchMinLen ? (
                    <p className="text-sm text-(--tgui--hint_color)">Ищем…</p>
                  ) : null}
                  {catalogSearchQuery.isError ? (
                    <p className="text-sm text-(--tgui--destructive_text_color)">
                      {catalogSearchQuery.error.message || 'Не удалось выполнить поиск'}
                    </p>
                  ) : null}
                  {resolveInlineError != null && (addKind === 'film' || addKind === 'game') ? (
                    <div className="rounded-xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_8%,transparent)] px-3 py-2.5">
                      <p className="text-sm text-(--tgui--destructive_text_color)">{resolveInlineError}</p>
                      <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                        <Button
                          mode="gray"
                          size="s"
                          stretched
                          type="button"
                          onClick={() => {
                            setResolveInlineError(null)
                            setAddKind('manual')
                            setManualFieldError(null)
                          }}
                        >
                          Создать вручную
                        </Button>
                        {addKind === 'film' && kinopoiskUrl.trim() !== '' ? (
                          <Button
                            mode="gray"
                            size="s"
                            stretched
                            type="button"
                            onClick={() => void handleResolveCatalogUrl()}
                            disabled={resolutionBusy}
                          >
                            Повторить по ссылке
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                  <Button
                    mode="gray"
                    stretched
                    type="button"
                    onClick={() => {
                      setResolveInlineError(null)
                      setAddKind('manual')
                      setManualFieldError(null)
                    }}
                  >
                    Создать вручную
                  </Button>
                  {catalogSearchHits.length > 0 ? (
                    <ul className="mt-1 flex max-h-80 flex-col gap-2 overflow-y-auto [-webkit-overflow-scrolling:touch]">
                      {catalogSearchHits.map((hit, idx) => {
                        const selectable = hit.catalog_item_id != null && !resolutionBusy
                        const rowKey = `${hit.provider}-${hit.external_id}-${hit.catalog_item_id ?? 'pending'}-${idx}`
                        const onActivate = (): void => {
                          if (!selectable || hit.catalog_item_id == null) return
                          if (addKind === 'film') void handleSelectKinopoiskSearchHit(hit)
                          else handleSelectRawgSearchHit(hit)
                        }
                        return (
                          <li key={rowKey}>
                            <button
                              type="button"
                              disabled={!selectable}
                              onClick={onActivate}
                              className="flex w-full gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3 text-left transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              <div className="h-16 w-12 shrink-0 overflow-hidden rounded-md bg-(--tgui--secondary_bg_color)">
                                {hit.cover_url ? (
                                  <img src={hit.cover_url} alt="" className="h-full w-full object-cover" />
                                ) : (
                                  <div className="flex h-full items-center justify-center text-[10px] text-(--tgui--hint_color)">
                                    —
                                  </div>
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-(--tgui--text_color)">{hit.title}</p>
                                {hit.subtitle ? (
                                  <p className="mt-0.5 line-clamp-2 text-xs text-(--tgui--hint_color)">
                                    {hit.subtitle}
                                  </p>
                                ) : null}
                                <p className="mt-1 text-[10px] uppercase tracking-wide text-(--tgui--hint_color)">
                                  {hit.source === 'local' ? 'в каталоге' : 'онлайн'}
                                  {hit.catalog_item_id == null ? ' · нет catalog_item_id' : null}
                                </p>
                              </div>
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  ) : null}
                  {catalogSearchQuery.isSuccess &&
                  debouncedCatalogSearch.length >= catalogSearchMinLen &&
                  catalogSearchHits.length === 0 &&
                  !catalogSearchQuery.isFetching ? (
                    <p className="text-sm text-(--tgui--hint_color)">
                      Ничего не нашли — уточните запрос, создайте вручную или откройте ввод по ссылке (Кинопоиск).
                    </p>
                  ) : null}
                  {catalogSearchQuery.hasNextPage ? (
                    <Button
                      mode="gray"
                      stretched
                      type="button"
                      disabled={catalogSearchQuery.isFetchingNextPage || resolutionBusy}
                      onClick={() => void catalogSearchQuery.fetchNextPage()}
                    >
                      {catalogSearchQuery.isFetchingNextPage ? 'Загружаем…' : 'Показать ещё'}
                    </Button>
                  ) : null}
                  {addKind === 'film' ? (
                    <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
                      <button
                        type="button"
                        className="text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                        onClick={() => setUrlShortcutOpen((v) => !v)}
                      >
                        {urlShortcutOpen ? 'Скрыть ввод по ссылке' : 'Или ссылка с Кинопоиска…'}
                      </button>
                      {urlShortcutOpen ? (
                        <div className="filmony-text-panel mt-3 border-t border-(--tgui--divider_color) pt-3">
                          <p className="text-xs leading-snug text-(--tgui--hint_color)">
                            Альтернатива поиску: вставьте полный URL страницы записи на Kinopoisk.
                          </p>
                          <label
                            htmlFor="create-card-kinopoisk-url"
                            className="mt-2 block text-xs font-medium text-(--tgui--hint_color)"
                          >
                            Адрес страницы
                          </label>
                          <input
                            id="create-card-kinopoisk-url"
                            type="url"
                            inputMode="url"
                            autoComplete="url"
                            enterKeyHint="go"
                            placeholder="https://www.kinopoisk.ru/…"
                            value={kinopoiskUrl}
                            onChange={(e) => {
                              setKinopoiskUrl(e.currentTarget.value)
                              setResolveInlineError(null)
                            }}
                            className={`mt-2 ${WIZARD_TEXT_FIELD_CLASS}`}
                          />
                          <div className="mt-3">
                            <Button stretched disabled={resolutionBusy} onClick={() => void handleResolveCatalogUrl()}>
                              {resolutionBusy ? 'Подтягиваем данные…' : 'Найти по ссылке и продолжить'}
                            </Button>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </>
              ) : null}

              {addKind === 'manual' ? (
                <>
                  <button
                    type="button"
                    className="self-start text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                    onClick={() => {
                      setAddKind(null)
                      setManualFieldError(null)
                    }}
                  >
                    ← Другой тип
                  </button>
                  <div
                    className="create-card-source-reveal"
                    role="region"
                    aria-label="Ручной ввод темы"
                  >
                    <p className="create-card-source-reveal-title">Своя тема</p>
                    <p className="create-card-source-reveal-body">
                      Если каталог не подошёл или это спектакль, подкаст и т.п. — укажите название и при желании обложку.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="create-card-manual-title" className="text-xs font-medium text-(--tgui--hint_color)">
                      Название
                    </label>
                    <input
                      id="create-card-manual-title"
                      type="text"
                      autoComplete="off"
                      placeholder="Например: название темы"
                      value={manualTitle}
                      onChange={(e) => {
                        setManualTitle(e.currentTarget.value)
                        setManualFieldError(null)
                      }}
                      className={WIZARD_TEXT_FIELD_CLASS}
                    />
                    {manualFieldError != null ? (
                      <p className="text-xs text-(--tgui--destructive_text_color)">{manualFieldError}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="create-card-manual-cover" className="text-xs font-medium text-(--tgui--hint_color)">
                      Обложка (необязательно)
                    </label>
                    <input
                      id="create-card-manual-cover"
                      type="url"
                      inputMode="url"
                      placeholder="https://…"
                      value={manualCoverUrl}
                      onChange={(e) => setManualCoverUrl(e.currentTarget.value)}
                      className={WIZARD_TEXT_FIELD_CLASS}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="create-card-manual-summary" className="text-xs font-medium text-(--tgui--hint_color)">
                      Коротко о чём (необязательно)
                    </label>
                    <textarea
                      id="create-card-manual-summary"
                      rows={3}
                      placeholder="Одно-два предложения"
                      value={manualSummary}
                      onChange={(e) => setManualSummary(e.currentTarget.value)}
                      className={`${WIZARD_TEXT_FIELD_CLASS} min-h-20 resize-y`}
                    />
                  </div>
                  <Button stretched disabled={resolutionBusy} onClick={() => handleManualContinue()}>
                    Дальше с этим названием
                  </Button>
                </>
              ) : null}
            </div>
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 2 ? (
          <WizardStepPanel title="2. Это нужная тема?">
            {confirmPreview != null ? (
              <div className="filmony-text-panel">
                {confirmPreview.showDupWarning ? (
                  <p className="filmony-text-panel mb-3 text-sm text-(--tgui--text_color)">
                    У вас уже есть карточка на эту тему в профиле.
                  </p>
                ) : (
                  <p className="filmony-text-panel mb-3 text-sm leading-snug text-(--tgui--hint_color)">
                    Проверьте обложку и название. Дальше вы поставите оценку и сможете добавить теги и заметку.
                  </p>
                )}
                {remixFromCard && !confirmPreview.showDupWarning ? (
                  <p className="filmony-text-panel mb-3 text-xs text-(--tgui--hint_color)">
                    По мотивам чужой карточки — у вас будет отдельная запись со своей оценкой.
                  </p>
                ) : null}
                <div className="filmony-text-panel flex gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
                  <div className="h-28 w-[4.5rem] shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                    {confirmPreview.posterUrl ? (
                      <img
                        src={confirmPreview.posterUrl}
                        alt={confirmPreview.title}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                        Нет обложки
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <Title level="3" weight="2">
                      {confirmPreview.title}
                    </Title>
                    <p className="mt-1 text-sm text-(--tgui--hint_color)">{confirmPreview.yearLabel}</p>
                    <FilmGenreChips genres={confirmPreview.genres} size="md" maxVisible={6} className="mt-2" />
                  </div>
                </div>
                {watchlistError != null ? (
                  <p className="mt-3 text-sm text-(--tgui--destructive_text_color)">{watchlistError}</p>
                ) : null}
                <div className="mt-5 flex flex-col gap-2">
                  {confirmPreview.showDupWarning ? (
                    <>
                      <Button
                        stretched
                        onClick={() => {
                          void navigate(`/cards/${Number(confirmPreview.myCardId)}`)
                        }}
                      >
                        Открыть мою карточку
                      </Button>
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          void navigate(`/cards/${Number(confirmPreview.myCardId)}/edit`)
                        }}
                      >
                        Редактировать карточку
                      </Button>
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          setCreationBinding(null)
                          setRemixFromCard(false)
                          setWatchlistError(null)
                          setManualTitle('')
                          setManualCoverUrl('')
                          setManualSummary('')
                          setKinopoiskUrl('')
                          setAddKind(null)
                          setStep(1)
                        }}
                      >
                        Выбрать другую тему
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button stretched onClick={() => setStep(3)}>
                        Всё верно, дальше
                      </Button>
                      {confirmPreview.showWatchlist ? (
                        <Button
                          mode="gray"
                          stretched
                          disabled={watchlistBusy}
                          onClick={() => void handleAddToWatchlist()}
                        >
                          {watchlistBusy ? 'Добавляем…' : 'Только в список «Позже»'}
                        </Button>
                      ) : null}
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          setCreationBinding(null)
                          setRemixFromCard(false)
                          setWatchlistError(null)
                          setManualTitle('')
                          setManualCoverUrl('')
                          setManualSummary('')
                          setKinopoiskUrl('')
                          setAddKind(null)
                          setStep(1)
                        }}
                      >
                        Изменить источник
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div className="filmony-text-panel">
                <p className="text-sm text-(--tgui--hint_color)">
                  Запись не найдена. Вернитесь к первому шагу и попробуйте снова.
                </p>
                <div className="mt-3">
                  <Button
                    stretched
                    onClick={() => {
                      setAddKind(null)
                      setStep(1)
                    }}
                  >
                    К выбору источника
                  </Button>
                </div>
              </div>
            )}
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 3 ? (
          <WizardStepPanel title="3. Оценка, настроение и полка">
            <div className="filmony-text-panel">
              <div className="filmony-text-panel text-center">
                <p className="text-sm font-medium text-(--tgui--text_color)">Ваша оценка</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">Шкала с шагом 0,5, максимум 10.</p>
                <p className="mt-2 text-4xl font-bold tabular-nums text-(--tgui--text_color)">{formatRating(rating)}</p>
                <div className="mt-3 flex justify-center gap-2">
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v - 0.5))}>
                    −0.5
                  </Button>
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v + 0.5))}>
                    +0.5
                  </Button>
                </div>
              </div>

              <div className="mt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">С кем делились впечатлением</p>
                {renderChoiceChips(COMPANY_OPTIONS, company, setCompany)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">Настроение до</p>
                {renderChoiceChips(MOOD_BEFORE_OPTIONS, moodBefore, setMoodBefore)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">Настроение после</p>
                {renderChoiceChips(MOOD_AFTER_OPTIONS, moodAfter, setMoodAfter)}
              </div>

              <div className="mt-5 border-t border-(--tgui--divider_color) pt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Полка в коллекции</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  Можно оставить автоматическую полку или выбрать свою. Новую полку создайте ниже — сообщения об
                  ошибке показываются только здесь.
                </p>
                {shelvesQuery.isLoading ? (
                  <p className="mt-2 text-xs text-(--tgui--hint_color)">Загрузка полок…</p>
                ) : shelvesQuery.isError ? (
                  <p className="filmony-text-panel mt-2 text-xs text-(--tgui--hint_color)">
                    Полки временно недоступны — можно продолжить: сервер подставит полку по умолчанию (без{' '}
                    <span className="font-mono text-[11px]">category_id</span>).
                  </p>
                ) : (
                  <>
                    <label htmlFor="create-card-shelf" className="sr-only">
                      Полка коллекции
                    </label>
                    <select
                      id="create-card-shelf"
                      className={`mt-3 ${WIZARD_TEXT_FIELD_CLASS}`}
                      value={selectedShelfId === null ? '' : String(selectedShelfId)}
                      onChange={(e) => {
                        const raw = e.currentTarget.value
                        setSelectedShelfId(raw === '' ? null : Number(raw))
                        setShelfError(null)
                      }}
                    >
                      <option value="">Авто (полка по умолчанию)</option>
                      {(shelvesQuery.data?.items ?? []).map((row) => (
                        <option key={row.id} value={String(row.id)}>
                          {row.name}
                        </option>
                      ))}
                    </select>
                    <div className="mt-2">
                      <button
                        type="button"
                        className="text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                        onClick={() => {
                          setShelfCreateExpanded((v) => !v)
                          setShelfError(null)
                        }}
                      >
                        {shelfCreateExpanded ? 'Скрыть создание полки' : '+ Новая полка'}
                      </button>
                      {shelfCreateExpanded ? (
                        <div className="mt-2 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
                          <p className="text-xs text-(--tgui--hint_color)">Имя новой полки</p>
                          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-stretch">
                            <input
                              type="text"
                              maxLength={120}
                              placeholder="Например: Триллеры 2025"
                              autoComplete="off"
                              value={newShelfDraft}
                              onChange={(e) => {
                                setNewShelfDraft(e.currentTarget.value)
                                setShelfError(null)
                              }}
                              className={`min-w-0 flex-1 ${WIZARD_TEXT_FIELD_CLASS}`}
                            />
                            <Button
                              mode="gray"
                              className="shrink-0 sm:self-stretch"
                              disabled={createShelfBusy}
                              type="button"
                              onClick={() => void submitNewShelf()}
                            >
                              {createShelfBusy ? '…' : 'Создать'}
                            </Button>
                          </div>
                          {shelfError != null ? (
                            <p className="mt-2 text-xs text-(--tgui--destructive_text_color)">{shelfError}</p>
                          ) : (
                            <p className="mt-2 text-xs text-(--tgui--hint_color)">
                              После создания она сразу станет выбранной для этой карточки.
                            </p>
                          )}
                        </div>
                      ) : null}
                    </div>
                  </>
                )}
              </div>

              <div className="mt-5">
                <Button
                  stretched
                  onClick={() => {
                    setSubmitError(null)
                    setStep(4)
                  }}
                >
                  Дальше к тегам и заметке
                </Button>
              </div>
            </div>
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 4 ? (
          <WizardStepPanel title="4. Теги, заметка и публикация">
            <div className="filmony-text-panel">
              <div>
                <p className="text-sm font-medium text-(--tgui--text_color)">Свои теги (до 5)</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">Короткие пометки об впечатлении — по желанию.</p>
              </div>
              {popularTagSuggestions.length > 0 ? (
                <div className="mt-3">
                  <p className="text-xs font-medium text-(--tgui--hint_color)">Часто у вас</p>
                  <div className="mt-1.5 flex gap-1.5 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
                    {popularTagSuggestions.map((row) => (
                      <button
                        key={row.tag}
                        type="button"
                        onClick={() => addTagFromSuggestion(row.tag)}
                        className="shrink-0 rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-1.5 text-xs text-(--tgui--text_color) active:opacity-90"
                      >
                        {row.tag}
                        <span className="ml-1 tabular-nums text-(--tgui--hint_color)">{row.use_count}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
              <div className="mt-3 flex flex-wrap items-stretch gap-2">
                <input
                  type="text"
                  placeholder="Добавить тег"
                  value={tagInput}
                  maxLength={MAX_CUSTOM_TAG_LEN + 8}
                  onChange={(e) => {
                    setTagInput(e.currentTarget.value)
                    setTagFieldError(null)
                  }}
                  className={`min-w-0 flex-1 ${WIZARD_TEXT_FIELD_CLASS}`}
                />
                <Button
                  mode="gray"
                  className="shrink-0 sm:self-stretch"
                  disabled={tagInputTooLong}
                  onClick={addTag}
                >
                  Добавить
                </Button>
              </div>
              {tagFieldError != null ? (
                <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">{tagFieldError}</p>
              ) : tagInputTooLong ? (
                <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">
                  Не больше {MAX_CUSTOM_TAG_LEN} символов в одном теге ({tagInput.trim().length}/
                  {MAX_CUSTOM_TAG_LEN})
                </p>
              ) : (
                <p className="mt-1.5 text-xs text-(--tgui--hint_color)">До {MAX_CUSTOM_TAG_LEN} символов в теге.</p>
              )}
              {inputPrefixSuggestions.length > 0 ? (
                <div
                  className="mt-2 max-h-40 overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) py-1"
                  role="listbox"
                  aria-label="Подходящие теги"
                >
                  {inputPrefixSuggestions.map((row) => (
                    <button
                      key={row.tag}
                      type="button"
                      role="option"
                      className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm text-(--tgui--text_color) hover:bg-(--tgui--secondary_bg_color)"
                      onClick={() => addTagFromSuggestion(row.tag)}
                    >
                      <span className="min-w-0 truncate">{row.tag}</span>
                      <span className="shrink-0 tabular-nums text-xs text-(--tgui--hint_color)">{row.use_count}</span>
                    </button>
                  ))}
                </div>
              ) : null}
              {customTags.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {customTags.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
                      onClick={() => removeTag(tag)}
                      title="Удалить тег"
                    >
                      {tag} ×
                    </button>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Теги необязательны — можно оставить пустыми.</p>
              )}

              <div className="mt-6 border-t border-(--tgui--divider_color) pt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Заметка к карточке</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  По желанию — до {MAX_WATCH_NOTE_LEN} символов. Реакции можно вставить кнопкой справа.
                </p>
                <div className="mt-2 flex gap-2">
                  <CommentDraftMultiline
                    ref={watchNoteRef}
                    value={watchNote}
                    onChange={(v) => {
                      setWatchNote(v)
                      setSubmitError(null)
                    }}
                    placeholder="Например: неожиданно тихий финал…"
                    ariaLabel="Заметка к карточке"
                    maxLength={MAX_WATCH_NOTE_LEN}
                    rows={4}
                    wrapperClassName="min-h-24 flex-1 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) outline-none transition-[border-color,box-shadow] focus-within:border-(--tgui--link_color) focus-within:ring-2 focus-within:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]"
                  />
                  <div className="flex shrink-0 flex-col justify-start pt-1">
                    <CommentReactionTokenPicker
                      allowInsert={watchNote.length < MAX_WATCH_NOTE_LEN}
                      onPickReactionTypeId={insertReactionIntoWatchNote}
                    />
                  </div>
                </div>
                {watchNoteTooLong ? (
                  <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">
                    Не больше {MAX_WATCH_NOTE_LEN} символов
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-(--tgui--hint_color)">
                    {watchNote.length}/{MAX_WATCH_NOTE_LEN}
                  </p>
                )}
              </div>

              <div className="mt-6 border-t border-(--tgui--divider_color) pt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Отправить подписчикам (по желанию)</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  Карточка создастся в любом случае; ниже можно сразу уведомить выбранных людей.
                </p>
                {sharePreview != null ? (
                  <div className="mt-3">
                    <ShareFollowersPicker
                      preview={{
                        posterUrl: sharePreview.posterUrl,
                        title: sharePreview.title,
                        yearLabel: sharePreview.yearLabel,
                      }}
                      followers={shareFollowers}
                      loading={shareFollowersLoading}
                      selected={shareSelected}
                      onToggle={toggleShareRecipient}
                    />
                  </div>
                ) : null}
                <div className="mt-4">
                  <p className="text-sm font-medium text-(--tgui--text_color)">Комментарий к уведомлению</p>
                  <p className="mt-1 text-xs text-(--tgui--hint_color)">
                    Текст для Telegram у выбранных подписчиков. До {MAX_WATCH_NOTE_LEN} символов.
                  </p>
                  <textarea
                    value={shareComment}
                    maxLength={MAX_WATCH_NOTE_LEN}
                    onChange={(e) => setShareComment(e.currentTarget.value)}
                    placeholder="Например: загляните в мини-апп — там детали"
                    rows={3}
                    className={`mt-2 ${WIZARD_TEXT_FIELD_CLASS} min-h-20 resize-y`}
                  />
                  <p className="mt-1 text-xs text-(--tgui--hint_color)">
                    {shareComment.length}/{MAX_WATCH_NOTE_LEN}
                  </p>
                </div>
              </div>

              {submitError != null ? (
                <p className="mt-5 text-sm text-(--tgui--destructive_text_color)">{submitError}</p>
              ) : null}
              <div className="mt-5">
                <Button
                  stretched
                  disabled={!canSubmitFinal || submitLoading}
                  onClick={() => void handleSubmit()}
                >
                  {submitLoading ? 'Создаём карточку…' : 'Создать карточку'}
                </Button>
              </div>
            </div>
          </WizardStepPanel>
        ) : null}
      </main>
    </div>
  )
}
