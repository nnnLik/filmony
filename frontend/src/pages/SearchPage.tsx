import { Avatar } from '@telegram-apps/telegram-ui'
import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router'

import {
  listCatalogFilms,
  type CatalogFilmItem,
  type CatalogFilmsPeriod,
  type CatalogFilmsSort,
} from '../api/catalogApi'
import {
  searchCatalog,
  searchSuggestions,
  type SearchSuggestionsResponse,
  type SearchUserItem,
} from '../api/searchApi'
import type { TasteQuizKnowledgeBatchItem } from '../api/tasteQuizTypes'
import type { StreakBatchItem } from '../api/streaksTypes'
import { ApiError, formatApiDetail } from '../api/client'
import { CatalogFilmsSection } from '../components/catalog/CatalogFilmsSection'
import type { CatalogRatedFilm } from '../components/catalog/CatalogRatedFilmRow'
import { UserSuggestionChipsStrip } from '../components/search/UserSuggestionChipsStrip'
import { SearchResultsSkeleton } from '../components/search/SearchResultsSkeleton'
import { TasteQuizCommentAuthorBadge } from '../components/tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../components/streaks/RatingStreakAuthorBadge'
import { InlineLoadingState } from '../components/ui/InlineLoadingState'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import { TabEmptyState } from '../components/ui/TabEmptyState'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useCursorInfiniteList } from '../hooks/useCursorInfiniteList'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { CATALOG_SEARCH_DEBOUNCE_MS } from '../lib/catalogSearchTiming'
import { formatQueryError } from '../lib/formatQueryError'
import { getMyProfile } from '../api/profileApi'
import { profileInitials } from '../lib/profileDisplay'
import { PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS } from '../lib/profileRatedCardsFilterOptions'
import { scheduleDeferredPepeDancingPrewarm, useHeaderPepeGifSrc } from '../lib/pepeGif'

import './SearchPage.css'

type SearchTab = 'cards' | 'people'

const SELECT_CLASS = PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS

const TAB_SEGMENTS: Array<{ value: SearchTab; label: string }> = [
  { value: 'cards', label: 'Карточки' },
  { value: 'people', label: 'Люди' },
]

const PERIOD_SEGMENTS: Array<{ value: CatalogFilmsPeriod; label: string }> = [
  { value: 'all_time', label: 'За всё время' },
  { value: 'month', label: 'За месяц' },
]

const SORT_OPTIONS: Array<{ value: CatalogFilmsSort; label: string }> = [
  { value: 'popularity', label: 'Популярные' },
  { value: 'avg_rating', label: 'Высший средний' },
]

function tabFromSearch(searchParams: URLSearchParams): SearchTab {
  const tab = searchParams.get('tab')
  return tab === 'people' ? 'people' : 'cards'
}

function userListLabel(u: SearchUserItem): string {
  if (u.display_name?.trim()) {
    return u.display_name.trim()
  }
  if (u.username?.trim()) {
    return `@${u.username.trim()}`
  }
  return `@${u.profile_slug}`
}

function toCatalogRatedFilm(item: CatalogFilmItem): CatalogRatedFilm {
  return {
    film_id: item.film_id,
    title: item.title,
    year: item.year,
    poster_url: item.poster_url,
    genres: item.genres,
    community_avg_rating: item.community_avg_rating,
    ratings_count: item.ratings_count,
  }
}

function UserSuggestionRow({
  user,
  knowledgeByOwnerId,
  streakByUserId,
  viewerId,
}: {
  user: SearchUserItem
  knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  viewerId: string | null
}) {
  const label = userListLabel(user)
  const initials = profileInitials({
    display_name: user.display_name,
    first_name: null,
    username: user.username,
  })
  return (
    <Link
      to={`/u/${encodeURIComponent(user.id)}`}
      className="flex min-h-[52px] items-center gap-3 rounded-xl px-2.5 py-2 no-underline text-(--tgui--text_color) transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] active:bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)]"
    >
      <Avatar size={40} src={user.photo_url ?? undefined} acronym={initials} />
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5">
          <div className="truncate font-medium">{label}</div>
          <TasteQuizCommentAuthorBadge
            knowledgeByAuthor={knowledgeByOwnerId}
            authorId={user.id}
            viewerId={viewerId}
          />
          <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={user.id} />
        </div>
        <div className="truncate text-sm text-(--tgui--hint_color)">@{user.profile_slug}</div>
      </div>
    </Link>
  )
}

function SearchSuggestionsBlocks({ data }: { data: SearchSuggestionsResponse }) {
  const hasAny =
    data.mutual_circle.length + data.popular_authors.length + data.random_with_cards.length > 0
  if (!hasAny) {
    return (
      <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-5 text-center">
        <p className="text-[14px] leading-relaxed text-(--tgui--hint_color)">
          Пока мало данных для подсказок — добавьте подписки и карточки, сообщество подрастёт.
        </p>
      </div>
    )
  }
  return (
    <div className="flex flex-col gap-3">
      <UserSuggestionChipsStrip
        title="Рядом с вашим кругом"
        hint="Те, с кем похожие подписки — возможные новые знакомства"
        users={data.mutual_circle}
      />
      <UserSuggestionChipsStrip
        title="Активные в ленте"
        hint="За последнюю неделю по новым карточкам"
        users={data.popular_authors}
      />
      <UserSuggestionChipsStrip
        title="Случайные с карточками"
        hint="Живой каталог — загляните в профиль"
        users={data.random_with_cards}
      />
    </div>
  )
}

function SearchTitleRow() {
  const headerPepeSrc = useHeaderPepeGifSrc()
  return (
    <div className="flex min-w-0 items-center gap-1.5">
      <h1 className="min-w-0 shrink truncate bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
        Поиск
      </h1>
      <img
        className="search-page__title-pepe"
        src={headerPepeSrc}
        alt=""
        width={28}
        height={28}
        decoding="async"
        aria-hidden
      />
    </div>
  )
}

function SearchField({
  id,
  placeholder,
  value,
  onChange,
}: {
  id: string
  placeholder: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div>
      <label htmlFor={id} className="sr-only">
        {placeholder}
      </label>
      <div className="flex items-center gap-2.5 rounded-2xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_24%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] px-3.5 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,.05)] transition-[border-color,box-shadow] duration-200 focus-within:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] focus-within:shadow-[0_0_0_3px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)]">
        <Search
          className="pointer-events-none size-5 shrink-0 text-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_75%,var(--tgui--hint_color))]"
          strokeWidth={2}
          aria-hidden
        />
        <input
          id={id}
          type="search"
          name="q"
          enterKeyHint="search"
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="min-w-0 flex-1 border-0 bg-transparent py-0.5 text-[16px] text-(--tgui--text_color) outline-none placeholder:text-(--tgui--hint_color)"
        />
      </div>
    </div>
  )
}

function ResultsSection({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,.03)]">
      <div className="mb-2 px-0.5">
        <h3 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-[12px] text-(--tgui--hint_color)">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  )
}

function SearchCardsPanel({
  sort,
  period,
  cardsQuery,
  debouncedCardsQuery,
  onSortChange,
  onPeriodChange,
  onCardsQueryChange,
  viewerId,
}: {
  sort: CatalogFilmsSort
  period: CatalogFilmsPeriod
  cardsQuery: string
  debouncedCardsQuery: string
  onSortChange: (sort: CatalogFilmsSort) => void
  onPeriodChange: (period: CatalogFilmsPeriod) => void
  onCardsQueryChange: (query: string) => void
  viewerId: string | null
}) {
  const catalogQ = debouncedCardsQuery.length >= 2 ? debouncedCardsQuery : undefined
  const isDebouncing = cardsQuery.trim().length >= 2 && cardsQuery.trim() !== debouncedCardsQuery

  const filmsQuery = useCursorInfiniteList({
    queryKey: ['catalog-films', sort, period, catalogQ ?? ''] as const,
    queryFn: ({ cursor, limit }) =>
      listCatalogFilms({ sort, period, q: catalogQ, cursor, limit }),
    enabled: true,
    limit: 20,
  })

  const films = useMemo(
    () => filmsQuery.items.map(toCatalogRatedFilm),
    [filmsQuery.items],
  )

  const filmsErr = formatQueryError(filmsQuery.error, 'Не удалось загрузить каталог фильмов')
  const showInitialLoading =
    (filmsQuery.isPending || isDebouncing) && films.length === 0 && filmsErr == null
  const showFilteredEmpty =
    catalogQ != null && filmsQuery.isSuccess && films.length === 0 && !filmsQuery.isFetching

  return (
    <div className="flex flex-col gap-4">
      <SegmentedControl
        value={period}
        onChange={onPeriodChange}
        segments={PERIOD_SEGMENTS}
        ariaLabel="Период каталога"
        layout="grid"
        gridColsClassName="grid-cols-2"
        size="sm"
      />

      <label className="block text-xs font-medium text-(--tgui--hint_color)">
        Сортировка
        <select
          className={`${SELECT_CLASS} mt-1`}
          value={sort}
          onChange={(e) => onSortChange(e.currentTarget.value as CatalogFilmsSort)}
          aria-label="Сортировка каталога"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <SearchField
        id="search-cards-input"
        placeholder="Название фильма…"
        value={cardsQuery}
        onChange={onCardsQueryChange}
      />

      {cardsQuery.trim().length > 0 && cardsQuery.trim().length < 2 ? (
        <p className="px-0.5 text-[12px] text-(--tgui--hint_color)">Ещё один символ — и покажем результаты.</p>
      ) : null}

      {showInitialLoading ? <InlineLoadingState message="Загружаем каталог…" /> : null}

      {filmsErr != null ? (
        <ListErrorState
          message={filmsErr}
          onRetry={() => {
            void filmsQuery.refetch()
          }}
        />
      ) : null}

      {showFilteredEmpty ? (
        <TabEmptyState
          fallback="Фильмов по этому запросу не нашли — попробуйте другое название."
          userId={viewerId}
          className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,transparent)] px-3 py-4"
        />
      ) : null}

      {!showInitialLoading && filmsErr == null && !showFilteredEmpty ? (
        <CatalogFilmsSection
          films={films}
          isPending={filmsQuery.isPending}
          emptyMessage="Пока нет оценённых фильмов в каталоге"
          hasNextPage={filmsQuery.hasNextPage}
          isFetchingNextPage={filmsQuery.isFetchingNextPage}
          onLoadMore={() => {
            void filmsQuery.fetchNextPage()
          }}
        />
      ) : null}
    </div>
  )
}

function SearchPeoplePanel({
  peopleQuery,
  debouncedPeopleQuery,
  onPeopleQueryChange,
  viewerId,
  knowledgeByOwnerId,
  streakByUserId,
  suggestionsQuery,
  searchQuery,
}: {
  peopleQuery: string
  debouncedPeopleQuery: string
  onPeopleQueryChange: (query: string) => void
  viewerId: string | null
  knowledgeByOwnerId: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  suggestionsQuery: UseQueryResult<SearchSuggestionsResponse>
  searchQuery: UseQueryResult<Awaited<ReturnType<typeof searchCatalog>>>
}) {
  const canSearch = debouncedPeopleQuery.length >= 2
  const isDebouncing = peopleQuery.trim().length >= 2 && peopleQuery.trim() !== debouncedPeopleQuery

  const suggestionsError =
    suggestionsQuery.isError && suggestionsQuery.error instanceof ApiError
      ? formatApiDetail(suggestionsQuery.error.detail)
      : suggestionsQuery.isError
        ? 'Не удалось загрузить подсказки'
        : null

  const searchError =
    searchQuery.isError && searchQuery.error instanceof ApiError
      ? formatApiDetail(searchQuery.error.detail)
      : searchQuery.isError
        ? 'Ошибка поиска'
        : null

  const users = searchQuery.data?.users ?? []
  const showSearchSkeleton =
    canSearch &&
    (isDebouncing || searchQuery.isPending || (searchQuery.isFetching && !searchQuery.isSuccess))
  const showUserEmpty = canSearch && searchQuery.isSuccess && users.length === 0

  return (
    <div className="flex flex-col gap-5">
      {!canSearch ? (
        <>
          {suggestionsQuery.isPending ? <InlineLoadingState message="Загружаем идеи для вас…" /> : null}
          {suggestionsError ? (
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-4">
              <p className="text-[14px] text-(--tgui--destructive_text_color)">{suggestionsError}</p>
            </div>
          ) : null}
          {suggestionsQuery.isSuccess && suggestionsQuery.data ? (
            <SearchSuggestionsBlocks data={suggestionsQuery.data} />
          ) : null}
        </>
      ) : null}

      <SearchField
        id="search-people-input"
        placeholder="Имя или @username…"
        value={peopleQuery}
        onChange={onPeopleQueryChange}
      />

      {!canSearch && peopleQuery.trim().length > 0 ? (
        <p className="px-0.5 text-[12px] text-(--tgui--hint_color)">Ещё один символ — и покажем результаты.</p>
      ) : null}

      {showSearchSkeleton ? <SearchResultsSkeleton /> : null}
      {searchError ? (
        <p className="px-0.5 text-[13px] text-(--tgui--destructive_text_color)">{searchError}</p>
      ) : null}

      {canSearch && searchQuery.isSuccess ? (
        <ResultsSection title="Люди" subtitle="По имени, нику или адресу профиля">
          {showUserEmpty ? (
            <TabEmptyState
              fallback="Пользователей с таким именем не нашли."
              userId={viewerId}
              className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,transparent)] px-3 py-4"
            />
          ) : (
            <div className="flex flex-col gap-0.5">
              {users.map((user) => (
                <UserSuggestionRow
                  key={user.id}
                  user={user}
                  knowledgeByOwnerId={knowledgeByOwnerId}
                  streakByUserId={streakByUserId}
                  viewerId={viewerId}
                />
              ))}
            </div>
          )}
        </ResultsSection>
      ) : null}
    </div>
  )
}

export function SearchPage() {
  const auth = useAuthStatus()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = tabFromSearch(searchParams)

  const initialCardsQuery =
    typeof location.state === 'object' &&
    location.state != null &&
    'cardsQuery' in location.state &&
    typeof (location.state as { cardsQuery?: unknown }).cardsQuery === 'string'
      ? (location.state as { cardsQuery: string }).cardsQuery.trim()
      : ''

  const [cardsQuery, setCardsQuery] = useState(initialCardsQuery)
  const [peopleQuery, setPeopleQuery] = useState('')
  const [debouncedCardsQuery, setDebouncedCardsQuery] = useState('')
  const [debouncedPeopleQuery, setDebouncedPeopleQuery] = useState('')
  const [sort, setSort] = useState<CatalogFilmsSort>('popularity')
  const [period, setPeriod] = useState<CatalogFilmsPeriod>('all_time')
  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)

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
    scheduleDeferredPepeDancingPrewarm()
  }, [])

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedCardsQuery(cardsQuery.trim()), CATALOG_SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(id)
  }, [cardsQuery])

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedPeopleQuery(peopleQuery.trim()), CATALOG_SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(id)
  }, [peopleQuery])

  const suggestionsQuery = useQuery({
    queryKey: ['search-suggestions'],
    queryFn: searchSuggestions,
    enabled: auth.kind === 'ready' && tab === 'people',
    staleTime: 5 * 60_000,
  })

  const peopleSearchQuery = useQuery({
    queryKey: ['search-catalog-users', debouncedPeopleQuery],
    queryFn: () => searchCatalog(debouncedPeopleQuery, { limit_cards: 0, limit_films: 0 }),
    enabled: auth.kind === 'ready' && tab === 'people' && debouncedPeopleQuery.length >= 2,
    staleTime: 30_000,
  })

  const tasteQuizOwnerIds = useMemo(() => {
    const ids = new Set<string>()
    const searchUsers = peopleSearchQuery.data?.users
    if (searchUsers != null) {
      for (const user of searchUsers) {
        ids.add(user.id)
      }
    }
    const suggestions = suggestionsQuery.data
    if (suggestions != null) {
      for (const user of suggestions.mutual_circle) ids.add(user.id)
      for (const user of suggestions.popular_authors) ids.add(user.id)
      for (const user of suggestions.random_with_cards) ids.add(user.id)
    }
    return [...ids]
  }, [peopleSearchQuery.data, suggestionsQuery.data])

  const { knowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(tasteQuizOwnerIds, {
    enabled: auth.kind === 'ready' && tasteQuizOwnerIds.length > 0,
  })
  const { streakByUserId } = useRatingStreaksOfUsers(tasteQuizOwnerIds, {
    enabled: auth.kind === 'ready' && tasteQuizOwnerIds.length > 0,
  })

  const setTab = (next: SearchTab) => {
    const nextParams = new URLSearchParams(searchParams)
    if (next === 'cards') {
      nextParams.delete('tab')
    } else {
      nextParams.set('tab', next)
    }
    setSearchParams(nextParams, { replace: true })
  }

  const headerSubtitle =
    tab === 'cards' ? 'Каталог фильмов сообщества' : 'Кого найти в сообществе Filmony'

  if (auth.kind === 'loading') {
    return <PageLoadingState authPending className="min-h-full bg-(--tgui--bg_color)" />
  }

  if (auth.kind !== 'ready') {
    return (
      <div className="min-h-full">
        <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
          <div className="px-4 py-3">
            <SearchTitleRow />
          </div>
        </header>
        <main className="px-4 pt-4">
          <p className="text-sm text-(--tgui--hint_color)">Войдите в приложение, чтобы пользоваться поиском.</p>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="px-4 py-3">
          <SearchTitleRow />
          <p className="mt-1 text-[13px] leading-snug text-(--tgui--hint_color)">{headerSubtitle}</p>
        </div>
      </header>

      <main className="max-w-full overflow-x-hidden px-4 pb-10 pt-4">
        <div className="flex flex-col gap-5">
          <SegmentedControl
            value={tab}
            onChange={setTab}
            segments={TAB_SEGMENTS}
            ariaLabel="Раздел поиска"
            layout="grid"
            gridColsClassName="grid-cols-2"
          />

          {tab === 'cards' ? (
            <SearchCardsPanel
              sort={sort}
              period={period}
              cardsQuery={cardsQuery}
              debouncedCardsQuery={debouncedCardsQuery}
              onSortChange={setSort}
              onPeriodChange={setPeriod}
              onCardsQueryChange={setCardsQuery}
              viewerId={viewerId}
            />
          ) : (
            <SearchPeoplePanel
              peopleQuery={peopleQuery}
              debouncedPeopleQuery={debouncedPeopleQuery}
              onPeopleQueryChange={setPeopleQuery}
              viewerId={viewerId}
              knowledgeByOwnerId={knowledgeByOwnerId}
              streakByUserId={streakByUserId}
              suggestionsQuery={suggestionsQuery}
              searchQuery={peopleSearchQuery}
            />
          )}
        </div>
      </main>
    </div>
  )
}
