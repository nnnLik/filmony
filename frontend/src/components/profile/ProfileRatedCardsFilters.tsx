import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Search } from 'lucide-react'
import { useState } from 'react'

import {
  getMyCardCategories,
  getUserMovieCardTags,
  getUserPublicCardCategories,
} from '../../api/profileApi'
import type { ProfileCardsSort } from '../../api/profileApi'
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
    enabled: profileUserId !== '',
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
    placeholderData: (): MyMovieCardTagStatsResponse | undefined =>
      readCachedUserMovieCardTagStats(profileUserId) ?? undefined,
  })

  const fetchShelvesEnabled =
    enableCategoryFilter && profileUserId !== '' && filtersOpen

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
  const shelvesErr: string | null =
    enableCategoryFilter && filtersOpen && shelvesQuery.isError
    ? shelvesQuery.error instanceof ApiError
      ? formatApiDetail(shelvesQuery.error.detail)
      : 'Не удалось загрузить полки'
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
              {hasActive && !filtersOpen ? ' · заданы условия' : ''}
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
