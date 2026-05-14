import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Search } from 'lucide-react'
import { useState } from 'react'

import { getMyCardCategories, getUserMovieCardTags } from '../../api/profileApi'
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
import { userMovieCardTagStatsQueryKey, myCardCategoriesQueryKey } from '../../feed/feedQueryKeys'
import {
  DEFAULT_RATED_CARDS_QUERY,
  type RatedCardsListQuery,
  isDefaultRatedCardsQuery,
} from '../../lib/ratedCardsListQuery'
import {
  readCachedUserMovieCardTagStats,
  writeCachedUserMovieCardTagStats,
} from '../../lib/movieCardTagStatsStorage'

const SORT_OPTIONS: Array<{ value: ProfileCardsSort; label: string }> = [
  { value: 'recent', label: 'Сначала новые' },
  { value: 'rating_desc', label: 'Оценка: выше' },
  { value: 'rating_asc', label: 'Оценка: ниже' },
]

function sortLabel(sort: ProfileCardsSort): string {
  return SORT_OPTIONS.find((o) => o.value === sort)?.label ?? sort
}

const COMPANY_OPTIONS: Array<{ value: CardCompany | ''; label: string }> = [
  { value: '', label: 'Кто угодно' },
  { value: 'alone', label: 'Один' },
  { value: 'partner', label: 'С партнёром' },
  { value: 'friends', label: 'С друзьями' },
  { value: 'family', label: 'С семьёй' },
]

const MOOD_BEFORE_OPTIONS: Array<{ value: CardMoodBefore | ''; label: string }> = [
  { value: '', label: 'Любое' },
  { value: 'relax', label: 'Расслабиться' },
  { value: 'laugh', label: 'Поржать' },
  { value: 'sad', label: 'Погрустить' },
  { value: 'thrill', label: 'Напряжение' },
]

const MOOD_AFTER_OPTIONS: Array<{ value: CardMoodAfter | ''; label: string }> = [
  { value: '', label: 'Любой итог' },
  { value: 'laughed', label: 'Весёлый' },
  { value: 'cried', label: 'Плакал' },
  { value: 'enjoyed', label: 'Кайфанул' },
  { value: 'tense', label: 'Уставший' },
  { value: 'wasted_time', label: 'Зря время' },
]

const SELECT_CLASS =
  'w-full rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2.5 py-2 text-sm text-(--tgui--text_color) outline-none ring-(--tgui--link_color) focus-visible:ring-2'

function filmTitleSearchValue(q: RatedCardsListQuery): string {
  return q.filmTitle
}

type ProfileRatedCardsFiltersProps = {
  profileUserId: string
  cardsQuery: RatedCardsListQuery
  onChange: (next: RatedCardsListQuery) => void
  /**
   * При `true`: показывает фильтр по полкам и грузит `GET /api/me/card-categories`
   * (имеет смысл только если список — ваш профиль; иначе id полок недоступны).
   */
  enableCategoryFilter?: boolean
}

export function ProfileRatedCardsFilters({
  profileUserId,
  cardsQuery,
  onChange,
  enableCategoryFilter = false,
}: ProfileRatedCardsFiltersProps) {
  const [filtersOpen, setFiltersOpen] = useState(false)

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

  const shelvesQuery = useQuery<MyUserCardCategoryListResponse>({
    queryKey: myCardCategoriesQueryKey(),
    queryFn: getMyCardCategories,
    enabled: enableCategoryFilter,
    staleTime: 60_000,
    gcTime: 30 * 60_000,
  })

  const shelfItems = shelvesQuery.data?.items ?? []
  const shelvesErr: string | null = enableCategoryFilter && shelvesQuery.isError
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
          <span className="sr-only">Среди оценённых фильмов этого профиля</span>
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
              value={filmTitleSearchValue(cardsQuery)}
              onChange={(e) => onChange({ ...cardsQuery, filmTitle: e.currentTarget.value })}
              className={`${SELECT_CLASS} pl-9`}
              autoComplete="off"
              aria-label="Поиск карточек по названию фильма"
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
              {filtersOpen ? 'Настройте список ниже' : sortLabel(cardsQuery.sort)}
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
          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Сортировка
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.sort}
              onChange={(e) => onChange({ ...cardsQuery, sort: e.currentTarget.value as ProfileCardsSort })}
              aria-label="Сортировка карточек"
            >
              {SORT_OPTIONS.map((o) => (
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
              ) : shelvesQuery.isLoading && shelfItems.length === 0 ? (
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
                aria-label="Минимальный год фильма"
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
                aria-label="Максимальный год фильма"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            С кем смотрел
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.company}
              onChange={(e) => onChange({ ...cardsQuery, company: e.currentTarget.value as CardCompany | '' })}
              aria-label="Фильтр: компания"
            >
              {COMPANY_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Хотел до просмотра
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.moodBefore}
              onChange={(e) => onChange({ ...cardsQuery, moodBefore: e.currentTarget.value as CardMoodBefore | '' })}
              aria-label="Фильтр: настроение до"
            >
              {MOOD_BEFORE_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs font-medium text-(--tgui--hint_color)">
            Итог просмотра
            <select
              className={`${SELECT_CLASS} mt-1`}
              value={cardsQuery.moodAfter}
              onChange={(e) => onChange({ ...cardsQuery, moodAfter: e.currentTarget.value as CardMoodAfter | '' })}
              aria-label="Фильтр: настроение после"
            >
              {MOOD_AFTER_OPTIONS.map((o) => (
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
