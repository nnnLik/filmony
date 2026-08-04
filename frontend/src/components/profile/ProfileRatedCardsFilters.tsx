import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'

import {
  getMyCardCategories,
  getUserMovieCardTags,
  getUserPublicCardCategories,
  getUserRatedDirectors,
} from '../../api/profileApi'
import { getGenresCatalogPage } from '../../api/genresApi'
import type { ProfileCardsSort, UserRatedDirectorsResponse } from '../../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MyMovieCardTagStatItem,
  MyMovieCardTagStatsResponse,
  MyUserCardCategoryListResponse,
} from '../../api/profileTypes'
import { ApiError, formatApiDetail } from '../../api/client'
import {
  userMovieCardTagStatsQueryKey,
  myCardCategoriesQueryKey,
  publicProfileCardCategoriesQueryKey,
  userRatedDirectorsQueryKey,
} from '../../feed/feedQueryKeys'
import {
  DEFAULT_RATED_CARDS_QUERY,
  type RatedCardsListQuery,
  isDefaultRatedCardsQuery,
} from '../../lib/ratedCardsListQuery'
import {
  readCachedUserMovieCardTagStats,
  writeCachedUserMovieCardTagStats,
} from '../../lib/movieCardTagStatsStorage'
import {
  readCachedMyCardCategories,
  readCachedPublicCardCategories,
  writeCachedMyCardCategories,
  writeCachedPublicCardCategories,
} from '../../lib/userCardCategoriesStorage'
import {
  PROFILE_RATED_COMPANY_OPTIONS,
  PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS,
  PROFILE_RATED_MOOD_AFTER_OPTIONS,
  PROFILE_RATED_MOOD_BEFORE_OPTIONS,
  PROFILE_RATED_CARDS_SORT_OPTIONS,
  profileRatedCardsSortLabel,
} from '../../lib/profileRatedCardsFilterOptions'

const SELECT_CLASS = `${PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS} w-full`

function ratedListTitleInputValue(q: RatedCardsListQuery): string {
  return q.filmTitle
}

type ProfileRatedCardsFiltersProps = {
  profileUserId: string
  /** Текущий зритель (вы); для совпадения с `profileUserId` грузим `/api/me/card-categories` (гарантирует дефолтную полку). */
  viewerUserId?: string | null
  cardsQuery: RatedCardsListQuery
  onChange: (next: RatedCardsListQuery) => void
  /**
   * При `true`: показывает фильтр по полкам — через `/api/me/...`, если профиль свой, иначе `GET /api/users/:id/card-categories`.
   */
  enableCategoryFilter?: boolean
}

export function ProfileRatedCardsFilters({
  profileUserId,
  viewerUserId = null,
  cardsQuery,
  onChange,
  enableCategoryFilter = false,
}: ProfileRatedCardsFiltersProps) {
  const [filtersOpen, setFiltersOpen] = useState(false)

  const useMyCardCategoriesLookup =
    enableCategoryFilter &&
    viewerUserId != null &&
    viewerUserId !== '' &&
    viewerUserId === profileUserId

  const tagsQuery = useQuery<MyMovieCardTagStatsResponse>({
    queryKey: userMovieCardTagStatsQueryKey(profileUserId),
    queryFn: async (): Promise<MyMovieCardTagStatsResponse> => {
      const res = await getUserMovieCardTags(profileUserId)
      writeCachedUserMovieCardTagStats(profileUserId, res)
      return res
    },
    enabled: profileUserId !== '' && (filtersOpen || cardsQuery.tags.length > 0),
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
    placeholderData: (): MyMovieCardTagStatsResponse | undefined =>
      readCachedUserMovieCardTagStats(profileUserId) ?? undefined,
  })

  const fetchShelvesEnabled =
    enableCategoryFilter && profileUserId !== '' && filtersOpen

  const fetchDirectorsEnabled =
    profileUserId !== '' && (filtersOpen || cardsQuery.directorKinopoiskId.trim() !== '')

  const fetchGenresEnabled = filtersOpen || cardsQuery.genre.trim() !== ''

  const directorsQuery = useQuery<UserRatedDirectorsResponse>({
    queryKey: userRatedDirectorsQueryKey(profileUserId),
    queryFn: () => getUserRatedDirectors(profileUserId),
    enabled: fetchDirectorsEnabled,
    staleTime: 15 * 60_000,
    gcTime: 60 * 60_000,
  })

  const genresQuery = useQuery({
    queryKey: ['genresCatalogFilter'],
    queryFn: () => getGenresCatalogPage({ limit: 100 }),
    enabled: fetchGenresEnabled,
    staleTime: 15 * 60_000,
    gcTime: 60 * 60_000,
  })

  const shelvesQuery = useQuery<MyUserCardCategoryListResponse>({
    queryKey: useMyCardCategoriesLookup
      ? myCardCategoriesQueryKey()
      : publicProfileCardCategoriesQueryKey(profileUserId),
    queryFn: async (): Promise<MyUserCardCategoryListResponse> => {
      const res = useMyCardCategoriesLookup
        ? await getMyCardCategories()
        : await getUserPublicCardCategories(profileUserId)
      if (useMyCardCategoriesLookup) {
        writeCachedMyCardCategories(res)
      } else {
        writeCachedPublicCardCategories(profileUserId, res)
      }
      return res
    },
    enabled: fetchShelvesEnabled,
    staleTime: 15 * 60_000,
    gcTime: 60 * 60_000,
    placeholderData: (): MyUserCardCategoryListResponse | undefined => {
      if (!fetchShelvesEnabled) {
        return undefined
      }
      if (useMyCardCategoriesLookup) {
        return readCachedMyCardCategories() ?? undefined
      }
      return readCachedPublicCardCategories(profileUserId) ?? undefined
    },
  })

  const shelfItems = shelvesQuery.data?.items ?? []
  const directorItems = useMemo(
    () => directorsQuery.data?.items ?? [],
    [directorsQuery.data?.items],
  )
  const genreItems = useMemo(() => genresQuery.data?.items ?? [], [genresQuery.data?.items])
  const shelvesErr: string | null =
    enableCategoryFilter && filtersOpen && shelvesQuery.isError
    ? shelvesQuery.error instanceof ApiError
      ? formatApiDetail(shelvesQuery.error.detail)
      : 'Не удалось загрузить полки'
    : null

  const directorsErr: string | null =
    filtersOpen && directorsQuery.isError
      ? directorsQuery.error instanceof ApiError
        ? formatApiDetail(directorsQuery.error.detail)
        : 'Не удалось загрузить режиссёров'
      : null

  const genresErr: string | null =
    filtersOpen && genresQuery.isError
      ? genresQuery.error instanceof ApiError
        ? formatApiDetail(genresQuery.error.detail)
        : 'Не удалось загрузить жанры'
      : null

  const tagItems: MyMovieCardTagStatItem[] = tagsQuery.data?.items ?? []
  const tagsErr: string | null = tagsQuery.isError
    ? tagsQuery.error instanceof ApiError
      ? formatApiDetail(tagsQuery.error.detail)
      : 'Не удалось загрузить теги'
    : null

  const toggleTag = (tag: string) => {
    const has = cardsQuery.tags.includes(tag)
    const nextTags = has ? cardsQuery.tags.filter((t) => t !== tag) : [...cardsQuery.tags, tag]
    onChange({ ...cardsQuery, tags: nextTags })
  }

  const hasActive = !isDefaultRatedCardsQuery(cardsQuery)

  const activeDirectorName = useMemo(() => {
    const id = cardsQuery.directorKinopoiskId.trim()
    if (id === '') {
      return null
    }
    const match = directorItems.find((row) => String(row.kinopoisk_id) === id)
    return match?.name ?? null
  }, [cardsQuery.directorKinopoiskId, directorItems])

  const activeGenreName = useMemo(() => {
    const slug = cardsQuery.genre.trim()
    if (slug === '') {
      return null
    }
    const match = genreItems.find((row) => row.slug === slug)
    return match?.genre ?? null
  }, [cardsQuery.genre, genreItems])

  const activeFilterHint = useMemo(() => {
    const parts: string[] = []
    if (activeDirectorName != null) {
      parts.push(`режиссёр: ${activeDirectorName}`)
    } else if (cardsQuery.directorKinopoiskId.trim() !== '') {
      parts.push('режиссёр')
    }
    if (activeGenreName != null) {
      parts.push(`жанр: ${activeGenreName}`)
    } else if (cardsQuery.genre.trim() !== '') {
      parts.push('жанр')
    }
    if (cardsQuery.franchiseKey.trim() !== '') {
      parts.push('франшиза')
    }
    if (cardsQuery.filmTitle.trim() !== '') {
      parts.push('поиск')
    }
    return parts.length > 0 ? parts.join(' · ') : null
  }, [
    activeDirectorName,
    activeGenreName,
    cardsQuery.directorKinopoiskId,
    cardsQuery.franchiseKey,
    cardsQuery.genre,
    cardsQuery.filmTitle,
  ])

  return (
    <div className="mb-3 overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
      <div className="border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] px-2.5 pt-2.5 pb-2">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-(--tgui--hint_color)">Поиск по названию</span>
          <span className="sr-only">Среди оценённых карточек этого профиля</span>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 block size-4 -translate-y-1/2 text-(--tgui--hint_color)"
              strokeWidth={1.75}
              aria-hidden
            />
            <input
              type="search"
              enterKeyHint="search"
              maxLength={120}
              placeholder="Например, матрица…"
              value={ratedListTitleInputValue(cardsQuery)}
              onChange={(e) => onChange({ ...cardsQuery, filmTitle: e.currentTarget.value })}
              className={`${SELECT_CLASS} pl-9`}
              autoComplete="off"
              aria-label="Поиск карточек по названию темы"
            />
          </div>
        </label>
      </div>
      <div className="flex items-stretch gap-2 p-2.5">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-2 rounded-xl px-1 py-1 text-left transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_8%,transparent)] active:opacity-90"
          onClick={() => setFiltersOpen((o) => !o)}
          aria-expanded={filtersOpen}
          aria-controls="profile-rated-cards-filters-panel"
          id="profile-rated-cards-filters-trigger"
        >
          <ChevronDown
            className={`block size-5 shrink-0 text-(--tgui--hint_color) transition-transform duration-200 ${filtersOpen ? 'rotate-180' : ''}`}
            strokeWidth={1.75}
            aria-hidden
          />
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold text-(--tgui--text_color)">Фильтры и сортировка</span>
            <span className="mt-0.5 block truncate text-[11px] text-(--tgui--hint_color)">
              {filtersOpen ? 'Настройте список ниже' : profileRatedCardsSortLabel(cardsQuery.sort)}
              {!filtersOpen && activeFilterHint != null ? ` · ${activeFilterHint}` : null}
              {hasActive && !filtersOpen && activeFilterHint == null ? ' · заданы условия' : null}
            </span>
          </span>
        </button>
        {hasActive ? (
          <Button
            type="button"
            mode="gray"
            size="s"
            className="shrink-0 self-center"
            onClick={() => onChange({ ...DEFAULT_RATED_CARDS_QUERY })}
          >
            Сбросить
          </Button>
        ) : null}
      </div>

      {filtersOpen ? (
        <div
          id="profile-rated-cards-filters-panel"
          role="region"
          aria-labelledby="profile-rated-cards-filters-trigger"
          className="space-y-3 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] px-3 pb-3 pt-3"
        >
          <div className="flex flex-wrap gap-2 text-xs">
            <Link to="/directors" className="font-medium text-(--tgui--link_color) no-underline">
              Все режиссёры →
            </Link>
            <Link to="/genres" className="font-medium text-(--tgui--link_color) no-underline">
              Каталог жанров →
            </Link>
          </div>

          <label className="flex flex-wrap items-center gap-2 rounded-xl px-1 py-1 text-xs font-medium text-(--tgui--hint_color)">
            <span className="grow basis-full">Только избранное</span>
            <input
              type="checkbox"
              className="size-4 accent-(--tgui--link_color)"
              checked={cardsQuery.favoritesOnly}
              onChange={(e) => onChange({ ...cardsQuery, favoritesOnly: e.currentTarget.checked })}
              aria-label="Показывать только карточки из избранного"
            />
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Сортировка
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.sort}
              onChange={(e) =>
                onChange({ ...cardsQuery, sort: e.currentTarget.value as ProfileCardsSort })
              }
              aria-label="Сортировка карточек"
            >
              {PROFILE_RATED_CARDS_SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          {enableCategoryFilter ? (
            <label className="block text-xs font-medium text-(--tgui--hint_color)">
              Полка
              <select
                className={`${SELECT_CLASS} mt-1`}
                value={cardsQuery.categoryId}
                onChange={(e) => onChange({ ...cardsQuery, categoryId: e.currentTarget.value })}
                aria-label="Фильтр: полка"
              >
                <option value="">Все полки</option>
                {shelfItems.map((row) => (
                  <option key={row.id} value={String(row.id)}>
                    {row.name}
                  </option>
                ))}
              </select>
              {shelvesErr != null ? (
                <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">{shelvesErr}</p>
              ) : shelvesQuery.isFetching && shelfItems.length === 0 ? (
                <p className="mt-1 text-xs text-(--tgui--hint_color)">Загрузка полок…</p>
              ) : null}
            </label>
          ) : null}

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Режиссёр
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.directorKinopoiskId}
              onChange={(e) =>
                onChange({
                  ...cardsQuery,
                  directorKinopoiskId: e.currentTarget.value,
                  franchiseKey: e.currentTarget.value !== '' ? '' : cardsQuery.franchiseKey,
                  genre: e.currentTarget.value !== '' ? '' : cardsQuery.genre,
                })
              }
              aria-label="Фильтр: режиссёр"
            >
              <option value="">Все режиссёры</option>
              {directorItems.map((row) => (
                <option key={row.kinopoisk_id} value={String(row.kinopoisk_id)}>
                  {row.name}
                  {row.count > 1 ? ` · ${row.count}` : ''}
                </option>
              ))}
            </select>
            {directorsErr != null ? (
              <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">{directorsErr}</p>
            ) : directorsQuery.isFetching && directorItems.length === 0 ? (
              <p className="mt-1 text-xs text-(--tgui--hint_color)">Загрузка режиссёров…</p>
            ) : null}
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Жанр
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.genre}
              onChange={(e) =>
                onChange({
                  ...cardsQuery,
                  genre: e.currentTarget.value,
                  directorKinopoiskId: e.currentTarget.value !== '' ? '' : cardsQuery.directorKinopoiskId,
                  franchiseKey: e.currentTarget.value !== '' ? '' : cardsQuery.franchiseKey,
                })
              }
              aria-label="Фильтр: жанр"
            >
              <option value="">Все жанры</option>
              {genreItems.map((row) => (
                <option key={row.slug} value={row.slug}>
                  {row.genre}
                  {row.films_count > 1 ? ` · ${row.films_count}` : ''}
                </option>
              ))}
            </select>
            {genresErr != null ? (
              <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">{genresErr}</p>
            ) : genresQuery.isFetching && genreItems.length === 0 ? (
              <p className="mt-1 text-xs text-(--tgui--hint_color)">Загрузка жанров…</p>
            ) : null}
          </label>

          <div className="grid grid-cols-2 gap-2">
            <label className="text-xs font-medium text-(--tgui--hint_color)">
              Год от
              <input
                type="number"
                inputMode="numeric"
                placeholder="—"
                className={`${SELECT_CLASS} mt-1 tabular-nums`}
                value={cardsQuery.yearMin}
                onChange={(e) => onChange({ ...cardsQuery, yearMin: e.currentTarget.value })}
                min={1874}
                max={2100}
                aria-label="Минимальный год (тема)"
              />
            </label>
            <label className="text-xs font-medium text-(--tgui--hint_color)">
              Год до
              <input
                type="number"
                inputMode="numeric"
                placeholder="—"
                className={`${SELECT_CLASS} mt-1 tabular-nums`}
                value={cardsQuery.yearMax}
                onChange={(e) => onChange({ ...cardsQuery, yearMax: e.currentTarget.value })}
                min={1874}
                max={2100}
                aria-label="Максимальный год (тема)"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Компания
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.company}
              onChange={(e) => onChange({ ...cardsQuery, company: e.currentTarget.value as CardCompany | '' })}
              aria-label="Фильтр: компания"
            >
              {PROFILE_RATED_COMPANY_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            До
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.moodBefore}
              onChange={(e) => onChange({ ...cardsQuery, moodBefore: e.currentTarget.value as CardMoodBefore | '' })}
              aria-label="Фильтр: настроение до"
            >
              {PROFILE_RATED_MOOD_BEFORE_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            После
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.moodAfter}
              onChange={(e) => onChange({ ...cardsQuery, moodAfter: e.currentTarget.value as CardMoodAfter | '' })}
              aria-label="Фильтр: настроение после"
            >
              {PROFILE_RATED_MOOD_AFTER_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <div>
            <p className="text-xs font-medium text-(--tgui--hint_color)">Теги автора (все выбранные)</p>
            {tagsErr != null ? (
              <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">{tagsErr}</p>
            ) : null}
            {tagItems.length === 0 && tagsErr == null && !tagsQuery.isFetching ? (
              <p className="mt-1 text-xs text-(--tgui--hint_color)">Нет сохранённых тегов</p>
            ) : (
              <div className="mt-1.5 flex max-h-28 flex-wrap gap-1 overflow-y-auto">
                {tagItems.map((row) => {
                  const on = cardsQuery.tags.includes(row.tag)
                  return (
                    <button
                      key={row.tag}
                      type="button"
                      title={`${row.use_count}×`}
                      onClick={() => toggleTag(row.tag)}
                      className={`max-w-40 truncate rounded-lg border px-2 py-1 text-[11px] font-medium transition-colors ${
                        on
                          ? 'border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] text-(--tgui--text_color)'
                          : 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--hint_color)'
                      }`}
                    >
                      {row.tag}
                      <span className="ml-1 tabular-nums opacity-70">{row.use_count}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
