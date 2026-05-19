import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Search } from 'lucide-react'
import { useState } from 'react'

import type { ProfileCardsSort } from '../../api/profileApi'
import { getMyCardCategories, getUserMovieCardTags } from '../../api/profileApi'
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
import {
  PROFILE_RATED_COMPANY_OPTIONS,
  PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS,
  PROFILE_RATED_MOOD_AFTER_OPTIONS,
  PROFILE_RATED_MOOD_BEFORE_OPTIONS,
  PROFILE_RATED_CARDS_SORT_OPTIONS,
  profileRatedCardsSortLabel,
} from '../../lib/profileRatedCardsFilterOptions'

const SELECT_CLASS = PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS

type ProfileStatsFiltersProps = {
  profileUserId: string
  cardsQuery: RatedCardsListQuery
  onChange: (next: RatedCardsListQuery) => void
  /**
   * Только когда открываете свой профиль: полки тянутся с `/api/me/card-categories`.
   */
  enableCategoryFilter?: boolean
}

export function ProfileStatsFilters({
  profileUserId,
  cardsQuery,
  onChange,
  enableCategoryFilter = false,
}: ProfileStatsFiltersProps) {
  const [moreOpen, setMoreOpen] = useState(false)

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
    <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
      <div className="flex flex-wrap items-start gap-x-2 gap-y-2 p-2.5">
        <span
          title="Единый период: API статистики не принимает даты фильтров"
          className="inline-flex shrink-0 items-center rounded-full border border-[color-mix(in_srgb,var(--tgui--divider_color)_62%,transparent)] bg-(--tgui--bg_color) px-2.5 py-1 text-[11px] font-medium text-(--tgui--hint_color)"
        >
          За всё время
        </span>

        <label className="flex min-w-36 max-w-full flex-[1_1_8rem] flex-col gap-0.5 text-[11px] font-medium text-(--tgui--hint_color)">
          Упорядочить как в карточках
          <select
            className={SELECT_CLASS}
            value={cardsQuery.sort}
            onChange={(e) => onChange({ ...cardsQuery, sort: e.currentTarget.value as ProfileCardsSort })}
            aria-label="Сортировка для списков и топов"
          >
            {PROFILE_RATED_CARDS_SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex min-w-30 shrink-0 items-center gap-2 rounded-xl border border-transparent px-1 py-0.5 text-[11px] font-medium text-(--tgui--hint_color)">
          <input
            type="checkbox"
            className="size-4 shrink-0 accent-(--tgui--link_color)"
            checked={cardsQuery.favoritesOnly}
            onChange={(e) => onChange({ ...cardsQuery, favoritesOnly: e.currentTarget.checked })}
            aria-label="Только карточки из избранного"
          />
          Только любимые
        </label>

        <button
          type="button"
          className="ml-auto flex min-w-0 max-w-full flex-[1_1_8rem] items-center gap-1.5 rounded-xl px-1 py-0.5 text-left text-[11px] font-medium text-(--tgui--link_color) transition-opacity active:opacity-80 sm:max-w-48"
          onClick={() => setMoreOpen((o) => !o)}
          aria-expanded={moreOpen}
          aria-controls="profile-stats-filters-extra"
          id="profile-stats-filters-trigger"
        >
          <ChevronDown
            className={`block size-4 shrink-0 transition-transform duration-200 ${moreOpen ? 'rotate-180' : ''}`}
            strokeWidth={2}
            aria-hidden
          />
          <span className="min-w-0 flex-1 truncate">{moreOpen ? 'Скрыть условия' : 'Подобрать по полям'}</span>
        </button>

        {hasActive ? (
          <Button
            type="button"
            mode="gray"
            size="s"
            className="shrink-0"
            onClick={() => onChange({ ...DEFAULT_RATED_CARDS_QUERY })}
          >
            Сбросить
          </Button>
        ) : null}
      </div>

      {moreOpen ? (
        <div
          id="profile-stats-filters-extra"
          role="region"
          aria-labelledby="profile-stats-filters-trigger"
          className="space-y-2.5 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] px-2.5 pt-2.5 pb-3"
        >
          <label className="block text-[11px] font-medium text-(--tgui--hint_color)">
            Название темы / поиск
            <div className="relative mt-0.5">
              <Search
                className="pointer-events-none absolute left-2.5 top-1/2 block size-3.5 -translate-y-1/2 text-(--tgui--hint_color)"
                strokeWidth={1.75}
                aria-hidden
              />
              <input
                type="search"
                enterKeyHint="search"
                maxLength={120}
                placeholder="Как на вкладке «Карточки»…"
                value={cardsQuery.filmTitle}
                onChange={(e) => onChange({ ...cardsQuery, filmTitle: e.currentTarget.value })}
                className={`${SELECT_CLASS} pl-8`}
                autoComplete="off"
                aria-label="Фильтр по названию"
              />
            </div>
          </label>

          {enableCategoryFilter ? (
            <label className="block text-[11px] font-medium text-(--tgui--hint_color)">
              Полка
              <select
                className={`${SELECT_CLASS} mt-0.5`}
                value={cardsQuery.categoryId}
                onChange={(e) => onChange({ ...cardsQuery, categoryId: e.currentTarget.value })}
                aria-label="Фильтр полка"
              >
                <option value="">Все полки</option>
                {shelfItems.map((row) => (
                  <option key={row.id} value={String(row.id)}>
                    {row.name}
                  </option>
                ))}
              </select>
              {shelvesErr != null ? (
                <p className="mt-0.5 text-[11px] text-(--tgui--destructive_text_color)">{shelvesErr}</p>
              ) : shelvesQuery.isLoading && shelfItems.length === 0 ? (
                <p className="mt-0.5 text-[11px] text-(--tgui--hint_color)">Загрузка полок…</p>
              ) : null}
            </label>
          ) : null}

          <div className="grid grid-cols-2 gap-x-2 gap-y-2">
            <label className="text-[11px] font-medium text-(--tgui--hint_color)">
              Год от
              <input
                type="number"
                inputMode="numeric"
                placeholder="—"
                className={`${SELECT_CLASS} mt-0.5 tabular-nums`}
                value={cardsQuery.yearMin}
                onChange={(e) => onChange({ ...cardsQuery, yearMin: e.currentTarget.value })}
                min={1874}
                max={2100}
              />
            </label>
            <label className="text-[11px] font-medium text-(--tgui--hint_color)">
              Год до
              <input
                type="number"
                inputMode="numeric"
                placeholder="—"
                className={`${SELECT_CLASS} mt-0.5 tabular-nums`}
                value={cardsQuery.yearMax}
                onChange={(e) => onChange({ ...cardsQuery, yearMax: e.currentTarget.value })}
                min={1874}
                max={2100}
              />
            </label>
          </div>

          <label className="block text-[11px] font-medium text-(--tgui--hint_color)">
            Компания
            <select
              className={`${SELECT_CLASS} mt-0.5`}
              value={cardsQuery.company}
              onChange={(e) => onChange({ ...cardsQuery, company: e.currentTarget.value as CardCompany | '' })}
              aria-label="Компания"
            >
              {PROFILE_RATED_COMPANY_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-[11px] font-medium text-(--tgui--hint_color)">
            До
            <select
              className={`${SELECT_CLASS} mt-0.5`}
              value={cardsQuery.moodBefore}
              onChange={(e) => onChange({ ...cardsQuery, moodBefore: e.currentTarget.value as CardMoodBefore | '' })}
            >
              {PROFILE_RATED_MOOD_BEFORE_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-[11px] font-medium text-(--tgui--hint_color)">
            После
            <select
              className={`${SELECT_CLASS} mt-0.5`}
              value={cardsQuery.moodAfter}
              onChange={(e) => onChange({ ...cardsQuery, moodAfter: e.currentTarget.value as CardMoodAfter | '' })}
            >
              {PROFILE_RATED_MOOD_AFTER_OPTIONS.map((o) => (
                <option key={o.value || 'any'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <div>
            <p className="text-[11px] font-medium text-(--tgui--hint_color)">Теги (пересечение)</p>
            {tagsErr != null ? (
              <p className="mt-0.5 text-[11px] text-(--tgui--destructive_text_color)">{tagsErr}</p>
            ) : null}
            {tagItems.length === 0 && tagsErr == null && !tagsQuery.isFetching ? (
              <p className="mt-0.5 text-[11px] text-(--tgui--hint_color)">Нет сохранённых тегов</p>
            ) : (
              <div className="mt-1 flex max-h-24 flex-wrap gap-1 overflow-y-auto">
                {tagItems.map((row) => {
                  const on = cardsQuery.tags.includes(row.tag)
                  return (
                    <button
                      key={row.tag}
                      type="button"
                      title={`${row.use_count}×`}
                      onClick={() => toggleTag(row.tag)}
                      className={`max-w-36 truncate rounded-lg border px-1.5 py-0.5 text-[11px] font-medium transition-colors ${
                        on
                          ? 'border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] text-(--tgui--text_color)'
                          : 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--hint_color)'
                      }`}
                    >
                      {row.tag}
                      <span className="ml-0.5 tabular-nums opacity-65">{row.use_count}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_70%,transparent)] px-2.5 py-2">
          <p className="text-[11px] leading-snug text-(--tgui--hint_color)">
            Сортировка <span className="font-semibold text-(--tgui--text_color)">{profileRatedCardsSortLabel(cardsQuery.sort)}</span>
            {' · '}списки согласованы с вкладкой «Карточки».
          </p>
        </div>
      )}
    </div>
  )
}
