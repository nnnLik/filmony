import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../../api/client'
import { getUserCards, getUserMovieCardStats } from '../../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  MovieCard,
  ProfileStatsMovieItem,
  TagDistributionItem,
  UserMovieCardStats,
  ValueDistributionItem,
} from '../../api/profileTypes'
import { profileStatsMoviePrimaryTitle } from '../../lib/movieCardDisplay'
import {
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
  ratedCardsToListParams,
  type RatedCardsListQuery,
} from '../../lib/ratedCardsListQuery'

import { StatsDistributionBars, TastePolarityChart } from './ProfileStatsCharts'
import { ProfileStatsMetricStrip, ProfileStatsSectionCard, ProfileStatsSummaryCard } from './ProfileStatsSummaryCard'

type ProfileStatsPanelProps = {
  userId: string
  cardsQuery: RatedCardsListQuery
  onCardsQueryChange: (next: RatedCardsListQuery) => void
  /** Фильтр полок доступен только владельцу профиля на вкладке карточек. */
  enableCategoryFilter?: boolean
  /** После действия из статистики — перейти к списку оценённых карточек (вкладка родителя). */
  onDrillToRatedCards?: () => void
}

const COMPANY_LABELS: Record<string, string> = {
  alone: 'Один',
  partner: 'С партнером',
  friends: 'С друзьями',
  family: 'С семьёй',
}

const MOOD_AFTER_LABELS: Record<string, string> = {
  laughed: 'Смеялся',
  cried: 'Плакал',
  enjoyed: 'Кайфанул',
  tense: 'Уставший',
  wasted_time: 'Зря время',
}

function formatRating(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function movieCardToProfileStatsMovieItem(card: MovieCard): ProfileStatsMovieItem {
  return {
    card_id: card.id,
    film_id: card.film_id,
    film_title: card.film_title,
    film_year: card.film_year,
    film_poster_url: card.film_poster_url,
    display_title: card.display_title,
    display_cover_url: card.display_cover_url ?? undefined,
    rating: card.rating,
  }
}

function StatsRatedCardRows({ items }: { items: ProfileStatsMovieItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
  }
  return (
    <div className="overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:rounded-2xl">
      <ul className="divide-y divide-(--tgui--divider_color)">
        {items.map((entry) => (
          <li key={entry.card_id}>
            <Link
              to={`/cards/${entry.card_id}`}
              className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm no-underline outline-none transition-[background-color,transform] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] active:scale-[0.998] focus-visible:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color) sm:py-3"
            >
              <div className="min-w-0">
                <p className="truncate text-(--tgui--text_color)">{profileStatsMoviePrimaryTitle(entry)}</p>
                <p className="text-xs text-(--tgui--hint_color)">{entry.film_year ?? 'Год неизвестен'}</p>
              </div>
              <span className="shrink-0 text-base font-semibold tabular-nums text-(--tgui--link_color) sm:text-lg">
                {formatRating(entry.rating)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

function splitPopularTags(tags: TagDistributionItem[], selected: readonly string[]): TagDistributionItem[] {
  if (selected.length === 0) {
    return tags
  }
  const setAll = new Set(selected)
  const hit = tags.filter((t) => setAll.has(t.tag))
  const miss = tags.filter((t) => !setAll.has(t.tag))
  return [...hit, ...miss]
}

export function ProfileStatsPanel({
  userId,
  cardsQuery,
  onCardsQueryChange,
  onDrillToRatedCards,
}: ProfileStatsPanelProps) {
  const [stats, setStats] = useState<UserMovieCardStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (userId === '') return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getUserMovieCardStats(userId)
        if (!alive) return
        setStats(data)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить статистику')
        }
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [userId])

  const needsFilteredRankings = !isDefaultRatedCardsQuery(cardsQuery)
  const rankingsKey = ratedCardsQueryKey(cardsQuery)

  const rankingsQuery = useQuery({
    queryKey: ['profile-stats-filtered-top', userId, rankingsKey],
    queryFn: async (): Promise<{ top: ProfileStatsMovieItem[]; worst: ProfileStatsMovieItem[] }> => {
      const base = ratedCardsToListParams(cardsQuery)
      const [bestPage, worstPage] = await Promise.all([
        getUserCards(userId, { ...base, limit: 50, sort: 'rating_desc' }),
        getUserCards(userId, { ...base, limit: 50, sort: 'rating_asc' }),
      ])
      return {
        top: bestPage.items.slice(0, 5).map(movieCardToProfileStatsMovieItem),
        worst: worstPage.items.slice(0, 5).map(movieCardToProfileStatsMovieItem),
      }
    },
    enabled: Boolean(userId) && needsFilteredRankings,
    staleTime: 45_000,
  })

  const ratingMax = useMemo(
    () => Math.max(0, ...(stats?.rating_distribution.map((item) => item.count) ?? [0])),
    [stats],
  )
  const yearMax = useMemo(
    () => Math.max(0, ...(stats?.year_distribution.map((item) => item.count) ?? [0])),
    [stats],
  )

  const shelfDistributionUi = useMemo(() => {
    const rows = stats?.category_distribution ?? []
    if (rows.length === 0) {
      return {
        hasShelves: false,
        shelfMax: 0,
        shelfUncatBarItems: [] as { label: string; count: number }[],
        shelfCatBarItems: [] as { label: string; count: number }[],
      }
    }
    const shelfMax = Math.max(0, ...rows.map((item) => item.count))
    const nameHits = new Map<string, number>()
    for (const row of rows) {
      nameHits.set(row.name, (nameHits.get(row.name) ?? 0) + 1)
    }
    const shelfUncatBarItems: { label: string; count: number }[] = []
    const shelfCatBarItems: { label: string; count: number }[] = []
    for (const row of rows) {
      if (row.category_id == null) {
        shelfUncatBarItems.push({ label: row.name, count: row.count })
      } else {
        const label =
          (nameHits.get(row.name) ?? 0) > 1 ? `${row.name} (#${row.category_id})` : row.name
        shelfCatBarItems.push({ label, count: row.count })
      }
    }
    return { hasShelves: true, shelfMax, shelfUncatBarItems, shelfCatBarItems }
  }, [stats])

  const ratingBarItems = useMemo(() => {
    const list = stats?.rating_distribution ?? []
    return [...list]
      .sort((a, b) => a.rating - b.rating)
      .map((item) => ({ label: String(item.rating), count: item.count }))
  }, [stats])

  const yearBarItems = useMemo(() => {
    const list = stats?.year_distribution ?? []
    return [...list]
      .sort((a, b) => a.year - b.year)
      .map((item) => ({ label: String(item.year), count: item.count }))
  }, [stats])

  const sentiment = useMemo(() => {
    const low = (stats?.rating_distribution ?? [])
      .filter((item) => item.rating <= 4)
      .reduce((acc, item) => acc + item.count, 0)
    const mid = (stats?.rating_distribution ?? [])
      .filter((item) => item.rating >= 5 && item.rating <= 7)
      .reduce((acc, item) => acc + item.count, 0)
    const high = (stats?.rating_distribution ?? [])
      .filter((item) => item.rating >= 8)
      .reduce((acc, item) => acc + item.count, 0)
    const total = low + mid + high
    const lowPct = total > 0 ? Math.round((low / total) * 100) : 0
    const midPct = total > 0 ? Math.round((mid / total) * 100) : 0
    const highPct = Math.max(0, 100 - lowPct - midPct)
    return { low, mid, high, total, midPct, highPct }
  }, [stats])

  const metricStripItems = useMemo(() => {
    const total = stats != null ? String(stats.total_movies) : '0'
    const avg = stats != null ? formatRating(stats.average_rating) : '0'
    return [
      { label: 'Карточек', value: total },
      { label: 'Средний балл', value: avg },
    ] as const
  }, [stats])

  const watchSummaryRows = useMemo(() => {
    const raw: ValueDistributionItem[] = stats?.watch_with_distribution ?? []
    const narrowed =
      cardsQuery.company === '' ? raw : raw.filter((item) => item.value === cardsQuery.company)
    return narrowed.map((item) => {
      const v = item.value as CardCompany
      return {
        label: COMPANY_LABELS[item.value] ?? item.value,
        value: String(item.count),
        onActivate: () => {
          const nextCompany: CardCompany | '' = cardsQuery.company === v ? '' : v
          onCardsQueryChange({ ...cardsQuery, company: nextCompany })
          onDrillToRatedCards?.()
        },
      }
    })
  }, [stats, cardsQuery, onCardsQueryChange, onDrillToRatedCards])

  const moodSummaryRows = useMemo(() => {
    const raw: ValueDistributionItem[] = stats?.mood_after_distribution ?? []
    const narrowed =
      cardsQuery.moodAfter === '' ? raw : raw.filter((item) => item.value === cardsQuery.moodAfter)
    return narrowed.map((item) => {
      const v = item.value as CardMoodAfter
      return {
        label: MOOD_AFTER_LABELS[item.value] ?? item.value,
        value: String(item.count),
        onActivate: () => {
          const nextMood: CardMoodAfter | '' = cardsQuery.moodAfter === v ? '' : v
          onCardsQueryChange({ ...cardsQuery, moodAfter: nextMood })
          onDrillToRatedCards?.()
        },
      }
    })
  }, [stats, cardsQuery, onCardsQueryChange, onDrillToRatedCards])

  const handleYearDistributionDrill = (label: string) => {
    const y = Number(label)
    if (!Number.isFinite(y)) return
    const yi = Math.trunc(y)
    onCardsQueryChange({
      ...cardsQuery,
      yearMin: String(yi),
      yearMax: String(yi),
    })
    onDrillToRatedCards?.()
  }

  const handleShelfDistributionDrill = (label: string) => {
    const rows = stats?.category_distribution ?? []
    if (rows.length === 0) return
    const nameHits = new Map<string, number>()
    for (const row of rows) {
      nameHits.set(row.name, (nameHits.get(row.name) ?? 0) + 1)
    }
    const hit = rows.find((row) => {
      if (row.category_id == null) return false
      const rowLabel =
        (nameHits.get(row.name) ?? 0) > 1 ? `${row.name} (#${row.category_id})` : row.name
      return rowLabel === label
    })
    if (hit == null || hit.category_id == null) return
    onCardsQueryChange({
      ...cardsQuery,
      categoryId: String(hit.category_id),
    })
    onDrillToRatedCards?.()
  }

  const prioritizedPopularTags = useMemo(() => {
    const base = stats?.popular_tags ?? []
    return splitPopularTags(base, cardsQuery.tags)
  }, [stats, cardsQuery.tags])

  const topMoviesDisplay = needsFilteredRankings
    ? (rankingsQuery.data?.top ?? [])
    : (stats?.top_movies ?? [])
  const worstMoviesDisplay = needsFilteredRankings
    ? (rankingsQuery.data?.worst ?? [])
    : (stats?.worst_movies ?? [])

  if (loading && stats == null) {
    return <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка статистики…</p>
  }
  if (error != null) {
    return <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
  }
  if (stats == null) {
    return null
  }

  const hasRatings = stats.rating_distribution.some((item) => item.count > 0)
  const rankingsLoading = needsFilteredRankings && rankingsQuery.isPending
  const rankingsErr =
    rankingsQuery.error instanceof ApiError
      ? formatApiDetail(rankingsQuery.error.detail)
      : rankingsQuery.error != null
        ? 'Не удалось загрузить списки по фильтру'
        : null

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-2.5 sm:p-3">
        <ProfileStatsMetricStrip metrics={metricStripItems} />
      </section>

      <ProfileStatsSectionCard title="Оценки по шкале">
        {hasRatings ? (
          <StatsDistributionBars items={ratingBarItems} maxCount={ratingMax} />
        ) : (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </ProfileStatsSectionCard>

      <ProfileStatsSectionCard title="Полярность оценок">
        {sentiment.total > 0 ? (
          <TastePolarityChart sentiment={sentiment} />
        ) : (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </ProfileStatsSectionCard>

      <ProfileStatsSectionCard title="Популярные теги">
        {prioritizedPopularTags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {prioritizedPopularTags.map((tag) => {
              const hilite = cardsQuery.tags.length > 0 && cardsQuery.tags.includes(tag.tag)
              const neutral = cardsQuery.tags.length === 0
              return (
                <button
                  key={tag.tag}
                  type="button"
                  aria-pressed={hilite}
                  aria-label={`Фильтр по тегу «${tag.tag}»`}
                  className={`max-w-[min(100%,12rem)] truncate rounded-lg border px-2 py-0.5 text-left text-[11px] leading-snug tabular-nums outline-none transition-[opacity,background-color] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) focus-visible:ring-offset-1 focus-visible:ring-offset-(--tgui--secondary_bg_color) active:opacity-90 ${
                    hilite
                      ? 'border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_16%,transparent)] text-(--tgui--text_color)'
                      : neutral
                        ? 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--text_color)'
                        : 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--text_color) opacity-60'
                  }`}
                  onClick={() => {
                    const has = cardsQuery.tags.includes(tag.tag)
                    const nextTags = has ? cardsQuery.tags.filter((t) => t !== tag.tag) : [...cardsQuery.tags, tag.tag]
                    onCardsQueryChange({ ...cardsQuery, tags: nextTags })
                    onDrillToRatedCards?.()
                  }}
                >
                  {tag.tag} <span className="text-(--tgui--hint_color)">({tag.count})</span>
                </button>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </ProfileStatsSectionCard>

      <ProfileStatsSectionCard title="По полкам">
        {shelfDistributionUi.hasShelves ? (
          <div className="flex w-full min-w-0 flex-col gap-2.5">
            {shelfDistributionUi.shelfUncatBarItems.length > 0 ? (
              <StatsDistributionBars
                items={shelfDistributionUi.shelfUncatBarItems}
                maxCount={shelfDistributionUi.shelfMax}
              />
            ) : null}
            {shelfDistributionUi.shelfCatBarItems.length > 0 ? (
              <StatsDistributionBars
                items={shelfDistributionUi.shelfCatBarItems}
                maxCount={shelfDistributionUi.shelfMax}
                onItemActivate={handleShelfDistributionDrill}
                itemActionHint="Показать карточки на полке"
              />
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </ProfileStatsSectionCard>

      {watchSummaryRows.length > 0 ? (
        <ProfileStatsSummaryCard title="Компания" rows={watchSummaryRows} />
      ) : (
        <ProfileStatsSectionCard title="Компания">
          <p className="text-sm text-(--tgui--hint_color)">
            {cardsQuery.company === '' ? 'Пока нет данных' : 'Нет совпадающего среза среди этого профиля.'}
          </p>
        </ProfileStatsSectionCard>
      )}

      {moodSummaryRows.length > 0 ? (
        <ProfileStatsSummaryCard title="После" rows={moodSummaryRows} />
      ) : (
        <ProfileStatsSectionCard title="После">
          <p className="text-sm text-(--tgui--hint_color)">
            {cardsQuery.moodAfter === '' ? 'Пока нет данных' : 'Нет строки настроения, совпадающей с фильтром.'}
          </p>
        </ProfileStatsSectionCard>
      )}

      {rankingsErr != null ? (
        <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">{rankingsErr}</p>
      ) : null}

      <ProfileStatsSectionCard title="Топ по оценке">
        {rankingsLoading ? <StatsRatedCardSkeleton /> : <StatsRatedCardRows items={topMoviesDisplay} />}
      </ProfileStatsSectionCard>

      <ProfileStatsSectionCard title="Самые низкие оценки">
        {rankingsLoading ? <StatsRatedCardSkeleton /> : <StatsRatedCardRows items={worstMoviesDisplay} />}
      </ProfileStatsSectionCard>

      <ProfileStatsSectionCard title="По годам выпуска">
        {stats.year_distribution.length > 0 ? (
          <StatsDistributionBars
            items={yearBarItems}
            maxCount={yearMax}
            onItemActivate={handleYearDistributionDrill}
            itemActionHint="Показать карточки за год"
          />
        ) : (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </ProfileStatsSectionCard>
    </div>
  )
}

function StatsRatedCardSkeleton() {
  return (
    <div className="space-y-2">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-3 sm:py-3.5"
        >
          <div className="h-4 w-2/3 rounded bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,transparent)]" />
          <div className="mt-2 h-3 w-24 rounded bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)]" />
        </div>
      ))}
    </div>
  )
}
