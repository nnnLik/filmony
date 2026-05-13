import { Button, Title } from '@telegram-apps/telegram-ui'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { inferCatalogProviderFromUrl, resolveCatalogByProviderUrl } from '../api/catalogApi'
import { createMovieCard, getFilmById, getMovieCardById, resolveFilmByKinopoiskUrl, shareMovieCardWithFollowers } from '../api/cardApi'
import {
  getMyMovieCardTagStats,
  getMyProfile,
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
import { safeHapticSuccess } from '../lib/safeHaptic'

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

type WizardStep = 1 | 2 | 3 | 4 | 5
const TOTAL_STEPS = 5
const STEP_TITLES: Record<WizardStep, string> = {
  1: 'Ссылка или название',
  2: 'Подтверждение',
  3: 'Оценка и контекст',
  4: 'Ваши теги',
  5: 'Поделиться',
}

type CreationBinding =
  | { kind: 'film'; film: Film }
  | { kind: 'catalog'; catalogItemId: number; film: Film }
  | {
      kind: 'manual'
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
    }

function watchlistFilmId(binding: CreationBinding): number | null {
  if (binding.kind === 'manual') return null
  return binding.film.id
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

function filmHasMyCard(f: Film): boolean {
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
    return 'Вставьте ссылку со страницы тайтла на Кинопоиске.'
  }
  if (normalized.includes('url must be from kinopoisk.ru')) {
    return 'Нужна ссылка с домена kinopoisk.ru.'
  }
  if (
    normalized.includes('kinopoisk id was not found in url') ||
    normalized.includes('film id was not found in url')
  ) {
    return 'Не получилось прочитать номер из ссылки. Скопируйте полный адрес со страницы фильма или сериала на Кинопоиске (из строки браузера).'
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
  const [kinopoiskUrl, setKinopoiskUrl] = useState('')
  const [loadingFilm, setLoadingFilm] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [watchlistBusy, setWatchlistBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
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

  const myTagStats: MyMovieCardTagStatItem[] = useMemo(
    () => tagStatsQuery.data?.items ?? [],
    [tagStatsQuery.data],
  )

  const skipFilmIdBootstrap = useMemo(() => {
    const raw = fromCardQuery
    return raw != null && raw !== ''
  }, [fromCardQuery])

  useEffect(() => {
    if (skipFilmIdBootstrap) {
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
      setLoadingFilm(true)
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
        setLoadingFilm(false)
      }
    })()
  }, [initialFilmId, skipFilmIdBootstrap])

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
      setLoadingFilm(true)
      setError(null)
      try {
        const [card, me] = await Promise.all([getMovieCardById(cardId), getMyProfile()])
        if (!alive || seq !== fromCardBootstrapSeq.current) return
        if (card.user_id != null && card.user_id === me.id) {
          setError('Свою карточку нельзя взять за основу — отредактируйте её или создайте новую по ссылке на Кинопоиск.')
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
        setLoadingFilm(false)
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
    if (step !== 5 || auth.kind !== 'ready') {
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
  const canProceedFromTags = !tagInputTooLong && !watchNoteTooLong

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
    const f = b.film
    return {
      posterUrl: f.poster_url ?? null,
      title: f.title,
      yearLabel: f.year != null ? String(f.year) : 'Год неизвестен',
      genres: f.genres ?? [],
      showDupWarning: filmHasMyCard(f),
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

  async function handleResolveFilm() {
    if (kinopoiskUrl.trim() === '') {
      setError('Вставьте ссылку на Кинопоиск')
      return
    }
    const trimmedUrl = kinopoiskUrl.trim()
    setLoadingFilm(true)
    setError(null)
    try {
      const provider = inferCatalogProviderFromUrl(trimmedUrl)
      if (provider != null) {
        try {
          const resolved = await resolveCatalogByProviderUrl(provider, trimmedUrl)
          setCreationBinding({ kind: 'catalog', catalogItemId: resolved.catalog_item_id, film: resolved.film })
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
        setError(mapResolveError(formatApiDetail(e.detail)))
      } else {
        setError('Не удалось получить данные по ссылке. Проверьте её и попробуйте снова.')
      }
    } finally {
      setLoadingFilm(false)
    }
  }

  function handleManualContinue() {
    const title = manualTitle.trim()
    if (title === '') {
      setError('Введите название тайтла')
      return
    }
    setError(null)
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

  async function handleAddToWatchlist() {
    if (creationBinding == null || creationBinding.kind === 'manual') {
      return
    }
    const fid = watchlistFilmId(creationBinding)
    if (fid == null || fid <= 0) {
      return
    }
    setWatchlistBusy(true)
    setError(null)
    try {
      await postMyWatchlistFilm(fid)
      clearMyProfileBundleCache()
      safeHapticSuccess()
      void navigate('/profile', { replace: true, state: { moviesSegment: 'watchlist' as const } })
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          setError('Эта запись уже в списке «к просмотру».')
          return
        }
        const msg = formatApiDetail(e.detail).toLowerCase()
        if (msg.includes('movie card already exists')) {
          setError('У вас уже есть оценённая карточка для этого тайтла.')
          return
        }
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось добавить в список')
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
      setError(`Тег не длиннее ${MAX_CUSTOM_TAG_LEN} символов`)
      return
    }
    const lowered = trimmed.toLowerCase()
    if (customTags.some((tag) => tag.toLowerCase() === lowered)) {
      setTagInput('')
      return
    }
    if (customTags.length >= 5) {
      setError('Можно добавить не больше 5 тегов')
      return
    }
    setCustomTags((prev) => [...prev, trimmed])
    setTagInput('')
    setError(null)
  }

  function addTagFromSuggestion(label: string) {
    const trimmed = label.trim()
    if (trimmed === '' || trimmed.length > MAX_CUSTOM_TAG_LEN) return
    const lowered = trimmed.toLowerCase()
    if (customTags.some((tag) => tag.toLowerCase() === lowered)) return
    if (customTags.length >= 5) {
      setError('Можно добавить не больше 5 тегов')
      return
    }
    setCustomTags((prev) => [...prev, trimmed])
    setTagInput('')
    setError(null)
  }

  function removeTag(tag: string) {
    setCustomTags((prev) => prev.filter((item) => item !== tag))
  }

  function goBack() {
    if (step === 1) {
      void navigate('/')
      return
    }
    setError(null)
    setStep((prev) => {
      const next = (prev - 1) as WizardStep
      if (next === 1) {
        setCreationBinding(null)
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
      setError('Сначала выберите тайтл')
      return
    }
    setSubmitLoading(true)
    setError(null)
    try {
      const watchNotePayload = watchNote.trim().slice(0, MAX_WATCH_NOTE_LEN)
      const ratingPayload = normalizeRating(rating)
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
        })
      } else if (creationBinding.kind === 'catalog') {
        newCard = await createMovieCard({
          catalog_item_id: creationBinding.catalogItemId,
          genres: [],
          rating: ratingPayload,
          company,
          mood_before: moodBefore,
          mood_after: moodAfter,
          custom_tags: customTags,
          watch_note: watchNotePayload,
        })
      } else {
        const m = creationBinding
        newCard = await createMovieCard({
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
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось создать карточку')
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
        {!fromCardPrefillDone ? (
          <p className="filmony-text-panel py-16 text-center text-sm text-(--tgui--hint_color)">
            Загружаем данные из карточки…
          </p>
        ) : null}

        {fromCardPrefillDone && step === 1 ? (
          <WizardStepPanel title="1. Ссылка или своё название">
            <div className="filmony-text-panel flex flex-col gap-4">
              <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-3">
                <p className="text-sm font-medium text-(--tgui--text_color)">Откуда взять ссылку</p>
                <ol className="mt-2 list-decimal space-y-2 pl-4 text-sm leading-snug text-(--tgui--hint_color)">
                  <li>Откройте на Кинопоиске страницу того, что смотрели (фильм или сериал).</li>
                  <li>
                    Скопируйте <span className="font-medium text-(--tgui--text_color)">весь адрес</span> из строки
                    браузера и вставьте ниже.
                  </li>
                </ol>
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="create-card-kinopoisk-url" className="text-xs font-medium text-(--tgui--hint_color)">
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
                  onChange={(e) => setKinopoiskUrl(e.currentTarget.value)}
                  className={WIZARD_TEXT_FIELD_CLASS}
                />
              </div>
              <Button stretched disabled={loadingFilm} onClick={() => void handleResolveFilm()}>
                {loadingFilm ? 'Загружаем...' : 'Далее по ссылке'}
              </Button>

              <div className="relative flex items-center gap-3 py-1">
                <div className="h-px flex-1 bg-(--tgui--divider_color)" />
                <span className="text-[11px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">или</span>
                <div className="h-px flex-1 bg-(--tgui--divider_color)" />
              </div>

              <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-3">
                <p className="text-sm font-medium text-(--tgui--text_color)">Без Кинопоиска</p>
                <p className="mt-1 text-xs leading-snug text-(--tgui--hint_color)">
                  Укажите название вручную — например сериал с другого сервиса или спектакль.
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
                  placeholder="Например: Название тайтла"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.currentTarget.value)}
                  className={WIZARD_TEXT_FIELD_CLASS}
                />
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
              <Button stretched disabled={loadingFilm} onClick={() => handleManualContinue()}>
                Далее без ссылки
              </Button>
            </div>
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 2 ? (
          <WizardStepPanel title="2. Подтверждение">
            {confirmPreview != null ? (
              <div className="filmony-text-panel">
                {confirmPreview.showDupWarning ? (
                  <p className="filmony-text-panel mb-3 text-sm text-(--tgui--text_color)">
                    У вас уже есть карточка на этот тайтл в профиле.
                  </p>
                ) : remixFromCard ? (
                  <p className="filmony-text-panel mb-3 text-xs text-(--tgui--hint_color)">
                    Своя оценка и теги — отдельная карточка у вас в профиле.
                  </p>
                ) : null}
                <div className="filmony-text-panel flex gap-3">
                  <div className="h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                    {confirmPreview.posterUrl ? (
                      <img
                        src={confirmPreview.posterUrl}
                        alt={confirmPreview.title}
                        className="h-full w-full object-cover"
                      />
                    ) : null}
                  </div>
                  <div className="min-w-0">
                    <Title level="3" weight="2">
                      {confirmPreview.title}
                    </Title>
                    <p className="mt-1 text-sm text-(--tgui--hint_color)">{confirmPreview.yearLabel}</p>
                    <FilmGenreChips genres={confirmPreview.genres} size="md" maxVisible={6} className="mt-2" />
                  </div>
                </div>
                <div className="mt-5 flex flex-col gap-2">
                  {confirmPreview.showDupWarning ? (
                    <>
                      <Button
                        stretched
                        onClick={() => {
                          void navigate(`/cards/${Number(confirmPreview.myCardId)}`)
                        }}
                      >
                        Открыть карточку
                      </Button>
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          void navigate(`/cards/${Number(confirmPreview.myCardId)}/edit`)
                        }}
                      >
                        Редактировать
                      </Button>
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          setCreationBinding(null)
                          setRemixFromCard(false)
                          setError(null)
                          setManualTitle('')
                          setManualCoverUrl('')
                          setManualSummary('')
                          setStep(1)
                        }}
                      >
                        Ввести другую ссылку
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button stretched onClick={() => setStep(3)}>
                        Оценить просмотр
                      </Button>
                      {confirmPreview.showWatchlist ? (
                        <Button
                          mode="gray"
                          stretched
                          disabled={watchlistBusy}
                          onClick={() => void handleAddToWatchlist()}
                        >
                          {watchlistBusy ? 'Добавляем…' : 'К просмотру'}
                        </Button>
                      ) : null}
                      <Button
                        mode="gray"
                        stretched
                        onClick={() => {
                          setCreationBinding(null)
                          setRemixFromCard(false)
                          setError(null)
                          setManualTitle('')
                          setManualCoverUrl('')
                          setManualSummary('')
                          setStep(1)
                        }}
                      >
                        Начать заново
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div className="filmony-text-panel">
                <p className="text-sm text-(--tgui--hint_color)">
                  Запись не найдена. Вернитесь к шагу 1 и введите ссылку снова.
                </p>
                <div className="mt-3">
                  <Button stretched onClick={() => setStep(1)}>
                    К шагу 1
                  </Button>
                </div>
              </div>
            )}
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 3 ? (
          <WizardStepPanel title="3. Оценка и теги">
            <div className="filmony-text-panel">
              <div className="filmony-text-panel text-center">
                <p className="text-sm text-(--tgui--hint_color)">Оценка</p>
                <p className="mt-1 text-4xl font-bold text-(--tgui--text_color)">{formatRating(rating)}</p>
                <div className="mt-3 flex justify-center gap-2">
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v - 0.5))}>
                    -0.5
                  </Button>
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v + 0.5))}>
                    +0.5
                  </Button>
                </div>
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">С кем смотрели:</p>
                {renderChoiceChips(COMPANY_OPTIONS, company, setCompany)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">До просмотра:</p>
                {renderChoiceChips(MOOD_BEFORE_OPTIONS, moodBefore, setMoodBefore)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">После просмотра:</p>
                {renderChoiceChips(MOOD_AFTER_OPTIONS, moodAfter, setMoodAfter)}
              </div>

              <div className="mt-5">
                <Button stretched onClick={() => setStep(4)}>
                  Далее
                </Button>
              </div>
            </div>
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 4 ? (
          <WizardStepPanel title="4. Ваши теги (до 5)">
            <div className="filmony-text-panel">
              {popularTagSuggestions.length > 0 ? (
                <div className="mb-3">
                  <p className="text-xs font-medium text-(--tgui--hint_color)">Частые теги</p>
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
              <div className="flex flex-wrap items-stretch gap-2">
                <input
                  type="text"
                  placeholder="Добавить тег"
                  value={tagInput}
                  maxLength={MAX_CUSTOM_TAG_LEN + 8}
                  onChange={(e) => {
                    setTagInput(e.currentTarget.value)
                    setError(null)
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
              {tagInputTooLong ? (
                <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">
                  Не больше {MAX_CUSTOM_TAG_LEN} символов в одном теге ({tagInput.trim().length}/{MAX_CUSTOM_TAG_LEN})
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
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Добавьте пару слов о впечатлении.</p>
              )}
              <div className="mt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Заметка о просмотре</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  По желанию: пару предложений о фильме. До {MAX_WATCH_NOTE_LEN} символов.
                </p>
                <div className="mt-2 flex gap-2">
                  <CommentDraftMultiline
                    ref={watchNoteRef}
                    value={watchNote}
                    onChange={(v) => {
                      setWatchNote(v)
                      setError(null)
                    }}
                    placeholder="Например: неожиданно тихий финал…"
                    ariaLabel="Заметка о просмотре"
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
              <div className="mt-5">
                <Button stretched disabled={!canProceedFromTags} onClick={() => setStep(5)}>
                  Далее
                </Button>
              </div>
            </div>
          </WizardStepPanel>
        ) : null}

        {fromCardPrefillDone && step === 5 ? (
          <WizardStepPanel title="5. Поделиться карточкой">
            <div className="filmony-text-panel">
              {sharePreview != null ? (
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
              ) : null}
              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">Комментарий к отправке</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  Попадёт в уведомление Telegram у выбранных подписчиков. До {MAX_WATCH_NOTE_LEN} символов.
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
              <div className="mt-5">
                <Button
                  stretched
                  disabled={creationBinding == null || submitLoading}
                  onClick={() => void handleSubmit()}
                >
                  {submitLoading ? 'Создаем...' : 'Готово'}
                </Button>
              </div>
            </div>
          </WizardStepPanel>
        ) : null}

        {error != null ? (
          <div className="mt-4 rounded-2xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_10%,transparent)] px-3 py-2">
            <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p>
          </div>
        ) : null}
      </main>
    </div>
  )
}
