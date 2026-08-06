import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'

import { ApiError, formatApiDetail } from '../../api/client'
import { getUserCards, getUserPublicCardCategories } from '../../api/profileApi'
import type {
  CardCompany,
  CardMoodAfter,
  MovieCard,
  ProfileInsightItem,
  ProfileStatsMovieItem,
  MyUserCardCategoryListResponse,
  TagDistributionItem,
  TagTasteItem,
  UserMovieCardStats,
  ValueDistributionItem,
} from '../../api/profileTypes'
import { profileStatsMoviePrimaryTitle } from '../../lib/movieCardDisplay'
import { mergeShelfDistributionWithMetadata } from '../../lib/profileShelfDistribution'
import {
  aggregateYearDistributionToDecades,
  COMPANY_DONUT_COLORS,
  DECADE_DONUT_COLORS,
  DIRECTOR_DONUT_COLORS,
  FRANCHISE_DONUT_COLORS,
  GENRE_DONUT_COLORS,
  findPeakRatedYear,
  MOOD_AFTER_DONUT_COLORS,
  RATING_DONUT_COLORS,
  SHELF_DONUT_COLORS,
  type DonutSegmentInput,
} from '../../lib/statsDonutChart'
import { genreSlug } from '../../lib/genreSlug'
import {
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
  ratedCardsToListParams,
  type RatedCardsListQuery,
} from '../../lib/ratedCardsListQuery'

import { ProfileActivityHeatmap } from './ProfileActivityHeatmap'
import {
  ProfileInsightsGrid,
  SocialTastePeers,
  StatsDonutChart,
  TagBubbleChart,
  TastePolarityChart,
} from './ProfileStatsCharts'
import { ProfileStatsMetricStrip, ProfileStatsSectionCard, ProfileStatsSummaryCard } from './ProfileStatsSummaryCard'
import { TasteQuizKnowledgeList } from '../tasteQuiz/TasteQuizKnowledgeList'
import { TabEmptyState } from '../ui/TabEmptyState'
import { listTasteQuizKnowledge } from '../../api/tasteQuizApi'
import type { TasteQuizKnowledgeItem } from '../../api/tasteQuizTypes'
import type { MarathonAchievement } from '../../api/gamificationTypes'
import { publicProfileCardCategoriesQueryKey } from '../../feed/feedQueryKeys'
import { profileStatsFilteredRankingsQueryKey } from '../../lib/profileQueryKeys'
import { useUserMovieCardStatsQuery } from '../../hooks/useUserMovieCardStatsQuery'
import { ProfilePassportPanel } from './gamification/ProfilePassportPanel'

type StatsSubTab = 'overview' | 'taste' | 'social' | 'rankings' | 'collection'

const STATS_SUB_TABS: { id: StatsSubTab; label: string }[] = [
  { id: 'overview', label: 'Обзор' },
  { id: 'taste', label: 'Вкус' },
  { id: 'social', label: 'Социальность' },
  { id: 'rankings', label: 'Рейтинги' },
  { id: 'collection', label: 'Коллекция' },
]

type ProfileStatsPanelProps = {
  userId: string
  cardsQuery: RatedCardsListQuery
  onCardsQueryChange: (next: RatedCardsListQuery) => void
  /** Фильтр полок доступен только владельцу профиля на вкладке карточек. */
  enableCategoryFilter?: boolean
  /** После действия из статистики — перейти к списку оценённых карточек (вкладка родителя). */
  onDrillToRatedCards?: () => void
  /** Блок «Угадай вкус» на вкладке «Социальность» (только свой профиль). */
  showTasteQuizTeaser?: boolean
  /** Показывать коллекцию штампов (свой профиль — полная, чужой — только открытые). */
  showPassportCollection?: boolean
  onMarathonDrill?: (marathon: MarathonAchievement) => void
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

function tagTasteFromStats(stats: UserMovieCardStats): TagTasteItem[] {
  if (stats.tag_taste != null && stats.tag_taste.length > 0) {
    return stats.tag_taste
  }
  return stats.popular_tags.map((t) => ({ tag: t.tag, count: t.count }))
}

function deriveInsights(
  stats: UserMovieCardStats,
  sentiment: { highPct: number; total: number },
): ProfileInsightItem[] {
  const snap = stats.insights
  const items: ProfileInsightItem[] = []
  if (snap != null) {
    if (snap.activity_total_180d > 0) {
      items.push({
        key: 'activity_180d',
        label: 'За 6 месяцев',
        value: String(snap.activity_total_180d),
        hint: 'завершённых просмотров',
      })
    }
    if (snap.top_director_name != null && snap.top_director_name !== '') {
      items.push({
        key: 'top_director',
        label: 'Любимый режиссёр',
        value: snap.top_director_name,
        hint:
          snap.top_director_count != null && snap.top_director_count > 0
            ? `${snap.top_director_count} ${snap.top_director_count === 1 ? 'фильм' : snap.top_director_count < 5 ? 'фильма' : 'фильмов'}`
            : undefined,
      })
    }
    if (snap.top_franchise_label != null && snap.top_franchise_label !== '') {
      items.push({
        key: 'top_franchise',
        label: 'Любимая серия',
        value: snap.top_franchise_label,
        hint:
          snap.top_franchise_count != null && snap.top_franchise_count > 0
            ? `${snap.top_franchise_count} ${snap.top_franchise_count === 1 ? 'фильм' : snap.top_franchise_count < 5 ? 'фильма' : 'фильмов'}`
            : undefined,
      })
    }
    if (snap.top_tag != null && snap.top_tag !== '') {
      items.push({ key: 'top_tag', label: 'Топ-тег', value: snap.top_tag })
    }
    if (snap.dominant_company != null && snap.dominant_company !== '') {
      items.push({
        key: 'company',
        label: 'Чаще всего',
        value: COMPANY_LABELS[snap.dominant_company] ?? snap.dominant_company,
        hint: 'компания',
      })
    }
    if (snap.dominant_mood_after != null && snap.dominant_mood_after !== '') {
      items.push({
        key: 'mood',
        label: 'После просмотра',
        value: MOOD_AFTER_LABELS[snap.dominant_mood_after] ?? snap.dominant_mood_after,
      })
    }
  } else {
    if (sentiment.total > 0) {
      items.push({
        key: 'high_pct',
        label: 'Высокие оценки',
        value: `${sentiment.highPct}%`,
        hint: '8–10 баллов',
      })
    }
    const topTag = stats.tag_taste?.[0] ?? stats.popular_tags[0]
    if (topTag != null) {
      items.push({
        key: 'top_tag',
        label: 'Топ-тег',
        value: topTag.tag,
        hint: `${topTag.count} раз`,
      })
    }
  }
  return items.slice(0, 4)
}

function StatsSubTabBar({
  active,
  onChange,
}: {
  active: StatsSubTab
  onChange: (tab: StatsSubTab) => void
}) {
  return (
    <div
      className="flex gap-1 overflow-x-auto rounded-full bg-(--tgui--secondary_bg_color) p-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="tablist"
      aria-label="Разделы статистики"
    >
      {STATS_SUB_TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          className={`shrink-0 rounded-full px-3 py-2 text-[11px] font-medium transition-all sm:text-xs ${
            active === tab.id
              ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
              : 'text-(--tgui--hint_color)'
          }`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export function ProfileStatsPanel({
  userId,
  cardsQuery,
  onCardsQueryChange,
  onDrillToRatedCards,
  showTasteQuizTeaser = false,
  showPassportCollection = false,
  onMarathonDrill,
}: ProfileStatsPanelProps) {
  const [statsSubTab, setStatsSubTab] = useState<StatsSubTab>('overview')
  const [activityShelfId, setActivityShelfId] = useState('')
  const [tasteQuizTeaserItems, setTasteQuizTeaserItems] = useState<TasteQuizKnowledgeItem[]>([])
  const [tasteQuizTeaserLoading, setTasteQuizTeaserLoading] = useState(false)

  const activityCategoryId = useMemo(() => {
    if (activityShelfId === '') {
      return null
    }
    const shelfNum = Number(activityShelfId)
    return Number.isInteger(shelfNum) && shelfNum >= 1 ? shelfNum : null
  }, [activityShelfId])

  const statsQuery = useUserMovieCardStatsQuery(userId, activityCategoryId, {
    enabled: userId !== '',
  })
  const stats = statsQuery.data ?? null
  const loading = statsQuery.isPending && stats == null
  const activityLoading = statsQuery.isFetching && stats != null
  const error =
    statsQuery.error instanceof ApiError
      ? formatApiDetail(statsQuery.error.detail)
      : statsQuery.error != null
        ? 'Не удалось загрузить статистику'
        : null

  const shelvesQuery = useQuery<MyUserCardCategoryListResponse>({
    queryKey: publicProfileCardCategoriesQueryKey(userId),
    queryFn: async (): Promise<MyUserCardCategoryListResponse> => getUserPublicCardCategories(userId),
    enabled: userId !== '',
    staleTime: 15 * 60_000,
  })

  useEffect(() => {
    queueMicrotask(() => {
      setActivityShelfId('')
    })
  }, [userId])

  useEffect(() => {
    if (!showTasteQuizTeaser || statsSubTab !== 'social') {
      return
    }
    let alive = true
    void (async () => {
      setTasteQuizTeaserLoading(true)
      try {
        const page = await listTasteQuizKnowledge('to_them', null, 5)
        if (!alive) return
        queueMicrotask(() => {
          if (!alive) return
          setTasteQuizTeaserItems(page.items)
        })
      } catch {
        if (!alive) return
        queueMicrotask(() => {
          if (!alive) return
          setTasteQuizTeaserItems([])
        })
      } finally {
        if (alive) setTasteQuizTeaserLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [showTasteQuizTeaser, statsSubTab])

  const needsFilteredRankings = !isDefaultRatedCardsQuery(cardsQuery)
  const rankingsKey = ratedCardsQueryKey(cardsQuery)

  const rankingsQuery = useQuery({
    queryKey: profileStatsFilteredRankingsQueryKey(userId, rankingsKey),
    queryFn: async (): Promise<{ top: ProfileStatsMovieItem[]; worst: ProfileStatsMovieItem[] }> => {
      const base = ratedCardsToListParams(cardsQuery)
      const [bestPage, worstPage] = await Promise.all([
        getUserCards(userId, { ...base, limit: 5, sort: 'rating_desc' }),
        getUserCards(userId, { ...base, limit: 5, sort: 'rating_asc' }),
      ])
      return {
        top: bestPage.items.map(movieCardToProfileStatsMovieItem),
        worst: worstPage.items.map(movieCardToProfileStatsMovieItem),
      }
    },
    enabled: Boolean(userId) && needsFilteredRankings,
    staleTime: 45_000,
  })

  const shelfDistributionRows = useMemo(
    () =>
      mergeShelfDistributionWithMetadata(
        stats?.category_distribution ?? [],
        shelvesQuery.data?.items ?? [],
      ),
    [stats?.category_distribution, shelvesQuery.data?.items],
  )

  const ratingDonutSegments = useMemo((): DonutSegmentInput[] => {
    const list = stats?.rating_distribution ?? []
    return [...list]
      .sort((a, b) => a.rating - b.rating)
      .map((item, idx) => ({
        label: String(item.rating),
        count: item.count,
        color: RATING_DONUT_COLORS[(item.rating - 1 + RATING_DONUT_COLORS.length) % RATING_DONUT_COLORS.length] ?? RATING_DONUT_COLORS[idx % RATING_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [stats])

  const decadeDonutSegments = useMemo((): DonutSegmentInput[] => {
    const buckets = aggregateYearDistributionToDecades(stats?.year_distribution ?? [])
    return buckets.map((bucket, idx) => ({
      label: bucket.label,
      count: bucket.count,
      value: bucket.value,
      color: DECADE_DONUT_COLORS[idx % DECADE_DONUT_COLORS.length] ?? '#5de1d4',
    }))
  }, [stats?.year_distribution])

  const genreDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = stats?.genre_distribution ?? []
    return rows
      .filter((item) => item.count > 0)
      .map((item, idx) => ({
        label: item.genre,
        count: item.count,
        value: genreSlug(item.genre),
        color: GENRE_DONUT_COLORS[idx % GENRE_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [stats?.genre_distribution])

  const directorDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = stats?.director_distribution ?? []
    return rows
      .filter((item) => item.count > 0)
      .map((item, idx) => ({
        label: item.name,
        count: item.count,
        value: String(item.kinopoisk_id),
        color: DIRECTOR_DONUT_COLORS[idx % DIRECTOR_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [stats?.director_distribution])

  const franchiseDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = stats?.franchise_distribution ?? []
    return rows
      .filter((item) => item.count > 0)
      .map((item, idx) => ({
        label: item.label,
        count: item.count,
        value: item.franchise_key,
        color: FRANCHISE_DONUT_COLORS[idx % FRANCHISE_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [stats?.franchise_distribution])

  const peakRatedYear = useMemo(
    () => findPeakRatedYear(stats?.rated_year_distribution),
    [stats?.rated_year_distribution],
  )

  const shelfDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = shelfDistributionRows
    if (rows.length === 0) return []

    const nameHits = new Map<string, number>()
    for (const row of rows) {
      nameHits.set(row.name, (nameHits.get(row.name) ?? 0) + 1)
    }

    return rows.map((row, idx) => {
      const label =
        row.category_id != null && (nameHits.get(row.name) ?? 0) > 1
          ? `${row.name} (#${row.category_id})`
          : row.name
      return {
        label,
        count: row.count,
        value: row.category_id != null ? String(row.category_id) : undefined,
        color: SHELF_DONUT_COLORS[idx % SHELF_DONUT_COLORS.length] ?? '#5de1d4',
      }
    })
  }, [shelfDistributionRows])

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
    const uniqueDirectors = stats?.insights?.unique_directors_count ?? 0
    const items = [
      { label: 'Карточек', value: total },
      { label: 'Средний балл', value: avg },
    ]
    if (uniqueDirectors > 0) {
      items.push({ label: 'Режиссёров', value: String(uniqueDirectors) })
    }
    return items
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

  const handleDecadeDistributionDrill = (decadeStartValue: string) => {
    const decadeStart = Number(decadeStartValue)
    if (!Number.isFinite(decadeStart)) return
    const start = Math.trunc(decadeStart)
    onCardsQueryChange({
      ...cardsQuery,
      yearMin: String(start),
      yearMax: String(start + 9),
    })
    onDrillToRatedCards?.()
  }

  const handleGenreDistributionDrill = (slug: string) => {
    const trimmed = slug.trim()
    if (trimmed === '') return
    onCardsQueryChange({
      ...cardsQuery,
      genre: trimmed,
      directorKinopoiskId: '',
      franchiseKey: '',
    })
    onDrillToRatedCards?.()
  }

  const handleDirectorDistributionDrill = (kinopoiskIdValue: string) => {
    const id = Number(kinopoiskIdValue)
    if (!Number.isInteger(id) || id < 1) return
    onCardsQueryChange({
      ...cardsQuery,
      directorKinopoiskId: String(id),
      genre: '',
      franchiseKey: '',
    })
    onDrillToRatedCards?.()
  }

  const handleFranchiseDistributionDrill = (franchiseKey: string) => {
    const trimmed = franchiseKey.trim()
    if (trimmed === '') return
    onCardsQueryChange({
      ...cardsQuery,
      franchiseKey: trimmed,
      genre: '',
      directorKinopoiskId: '',
    })
    onDrillToRatedCards?.()
  }

  const handleShelfDistributionDrill = (categoryIdValue: string) => {
    const categoryId = Number(categoryIdValue)
    if (!Number.isInteger(categoryId) || categoryId < 1) return
    onCardsQueryChange({
      ...cardsQuery,
      categoryId: String(categoryId),
    })
    onDrillToRatedCards?.()
  }

  const prioritizedPopularTags = useMemo(() => {
    const base = stats?.popular_tags ?? []
    return splitPopularTags(base, cardsQuery.tags)
  }, [stats, cardsQuery.tags])

  const tagTasteItems = useMemo(() => (stats != null ? tagTasteFromStats(stats) : []), [stats])

  const insightItems = useMemo(
    () => (stats != null ? deriveInsights(stats, sentiment) : []),
    [stats, sentiment],
  )

  const companyDonutSegments = useMemo((): DonutSegmentInput[] => {
    const raw = stats?.watch_with_distribution ?? []
    const narrowed = cardsQuery.company === '' ? raw : raw.filter((item) => item.value === cardsQuery.company)
    return narrowed.map((item, idx) => ({
      label: COMPANY_LABELS[item.value] ?? item.value,
      count: item.count,
      value: item.value,
      color: COMPANY_DONUT_COLORS[idx % COMPANY_DONUT_COLORS.length] ?? '#5de1d4',
    }))
  }, [stats, cardsQuery.company])

  const moodDonutSegments = useMemo((): DonutSegmentInput[] => {
    const raw = stats?.mood_after_distribution ?? []
    const narrowed = cardsQuery.moodAfter === '' ? raw : raw.filter((item) => item.value === cardsQuery.moodAfter)
    return narrowed.map((item, idx) => ({
      label: MOOD_AFTER_LABELS[item.value] ?? item.value,
      count: item.count,
      value: item.value,
      color: MOOD_AFTER_DONUT_COLORS[idx % MOOD_AFTER_DONUT_COLORS.length] ?? '#5de1d4',
    }))
  }, [stats, cardsQuery.moodAfter])

  const tastePeers = stats?.social?.taste_peers ?? []
  const mutualSubscriptionsCount = stats?.social?.mutual_subscriptions_count ?? 0

  const topMoviesDisplay = needsFilteredRankings
    ? (rankingsQuery.data?.top ?? [])
    : (stats?.top_movies ?? [])
  const worstMoviesDisplay = needsFilteredRankings
    ? (rankingsQuery.data?.worst ?? [])
    : (stats?.worst_movies ?? [])

  const handleActivityDaySelect = (isoDate: string, shelfId: string) => {
    onCardsQueryChange({
      ...cardsQuery,
      completedOn: isoDate,
      categoryId: shelfId,
      sort: 'recent',
    })
    onDrillToRatedCards?.()
  }

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
      <StatsSubTabBar active={statsSubTab} onChange={setStatsSubTab} />

      {statsSubTab === 'overview' ? (
        <>
          <ProfileActivityHeatmap
            activity={stats.activity_distribution}
            activityStart={stats.activity_start}
            activityEnd={stats.activity_end}
            shelves={shelfDistributionRows}
            selectedShelfId={activityShelfId}
            onShelfChange={setActivityShelfId}
            loading={activityLoading}
            onDaySelect={handleActivityDaySelect}
          />

          <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-2.5 sm:p-3">
            <ProfileStatsMetricStrip metrics={metricStripItems} />
          </section>

          {insightItems.length > 0 ? (
            <ProfileStatsSectionCard title="Инсайты">
              <ProfileInsightsGrid items={insightItems} />
            </ProfileStatsSectionCard>
          ) : null}

          <ProfileStatsSectionCard title="Полярность оценок">
            {sentiment.total > 0 ? (
              <TastePolarityChart sentiment={sentiment} />
            ) : (
              <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
            )}
          </ProfileStatsSectionCard>
        </>
      ) : null}

      {statsSubTab === 'taste' ? (
        <>
          <ProfileStatsSectionCard title="Оценки по шкале">
            {hasRatings ? (
              <StatsDonutChart segments={ratingDonutSegments} />
            ) : (
              <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
            )}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="Теги вкуса">
            <TagBubbleChart
              items={tagTasteItems}
              selectedTags={cardsQuery.tags}
              onTagClick={(tag) => {
                const has = cardsQuery.tags.includes(tag)
                const nextTags = has ? cardsQuery.tags.filter((t) => t !== tag) : [...cardsQuery.tags, tag]
                onCardsQueryChange({ ...cardsQuery, tags: nextTags })
                onDrillToRatedCards?.()
              }}
            />
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="Компания">
            <StatsDonutChart
              segments={companyDonutSegments}
              activeValue={cardsQuery.company === '' ? undefined : cardsQuery.company}
              onSegmentClick={(value) => {
                const v = value as CardCompany
                const nextCompany: CardCompany | '' = cardsQuery.company === v ? '' : v
                onCardsQueryChange({ ...cardsQuery, company: nextCompany })
                onDrillToRatedCards?.()
              }}
            />
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="После просмотра">
            <StatsDonutChart
              segments={moodDonutSegments}
              activeValue={cardsQuery.moodAfter === '' ? undefined : cardsQuery.moodAfter}
              onSegmentClick={(value) => {
                const v = value as CardMoodAfter
                const nextMood: CardMoodAfter | '' = cardsQuery.moodAfter === v ? '' : v
                onCardsQueryChange({ ...cardsQuery, moodAfter: nextMood })
                onDrillToRatedCards?.()
              }}
            />
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="По полкам">
            {shelfDonutSegments.length > 0 ? (
              <StatsDonutChart
                segments={shelfDonutSegments}
                activeValue={cardsQuery.categoryId === '' ? undefined : cardsQuery.categoryId}
                onSegmentClick={handleShelfDistributionDrill}
              />
            ) : (
              <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
            )}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="По жанрам">
            {genreDonutSegments.length > 0 ? (
              <div className="space-y-3">
                <StatsDonutChart
                  segments={genreDonutSegments}
                  legendCollapsedTopN={8}
                  onSegmentClick={handleGenreDistributionDrill}
                  activeValue={cardsQuery.genre === '' ? undefined : cardsQuery.genre}
                />
                <Link
                  to="/genres"
                  className="block text-center text-sm text-(--tgui--link_color) no-underline"
                >
                  Все жанры →
                </Link>
              </div>
            ) : (
              <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
            )}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="По режиссёрам">
            {directorDonutSegments.length > 0 ? (
              <div className="space-y-3">
                <StatsDonutChart
                  segments={directorDonutSegments}
                  legendCollapsedTopN={8}
                  onSegmentClick={handleDirectorDistributionDrill}
                  activeValue={
                    cardsQuery.directorKinopoiskId === ''
                      ? undefined
                      : cardsQuery.directorKinopoiskId
                  }
                />
                <Link
                  to="/directors"
                  className="block text-center text-sm text-(--tgui--link_color) no-underline"
                >
                  Все режиссёры →
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-(--tgui--hint_color)">
                  Режиссёры появятся, когда в карточках будут фильмы с метаданными Кинопоиска.
                </p>
                <TabEmptyState
                  fallback="Оцените фильм с режиссёром — мы построим распределение автоматически."
                  userId={userId}
                  action={{ label: 'Добавить карточку', href: '/cards/new' }}
                  className="py-4"
                />
              </div>
            )}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="По сериям">
            {franchiseDonutSegments.length > 0 ? (
              <StatsDonutChart
                segments={franchiseDonutSegments}
                legendCollapsedTopN={8}
                onSegmentClick={handleFranchiseDistributionDrill}
                activeValue={cardsQuery.franchiseKey === '' ? undefined : cardsQuery.franchiseKey}
              />
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-(--tgui--hint_color)">
                  Серии и франшизы подтягиваются из метаданных фильмов в ваших карточках.
                </p>
                <TabEmptyState
                  fallback="Оцените фильм из серии — здесь появится распределение по франшизам."
                  userId={userId}
                  action={{ label: 'Добавить карточку', href: '/cards/new' }}
                  className="py-4"
                />
              </div>
            )}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="По десятилетиям">
            {decadeDonutSegments.length > 0 ? (
              <div className="flex w-full min-w-0 flex-col gap-4">
                <StatsDonutChart
                  segments={decadeDonutSegments}
                  legendCollapsedTopN={8}
                  onSegmentClick={handleDecadeDistributionDrill}
                />
                {peakRatedYear != null ? (
                  <div className="rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,var(--tgui--bg_color))] px-3 py-2.5 shadow-[0_0_0_1px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)]">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">
                      Пик активности
                    </p>
                    <p className="mt-1 text-sm text-(--tgui--text_color)">
                      Больше всего оценок в{' '}
                      <span className="font-semibold tabular-nums">{peakRatedYear.year}</span>
                    </p>
                    <p className="mt-0.5 text-xs tabular-nums text-(--tgui--hint_color)">
                      {peakRatedYear.count} {peakRatedYear.count === 1 ? 'оценка' : peakRatedYear.count < 5 ? 'оценки' : 'оценок'}
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
            )}
          </ProfileStatsSectionCard>
        </>
      ) : null}

      {statsSubTab === 'social' ? (
        <>
          {showTasteQuizTeaser ? (
            <ProfileStatsSectionCard title="Угадай вкус">
              <TasteQuizKnowledgeList
                items={tasteQuizTeaserItems}
                emptyCopy="Вы ещё ни с кем не играли. Подпишитесь на друзей и нажмите «Угадать вкус» в их профиле."
                loading={tasteQuizTeaserLoading}
              />
              <Link
                to="/taste-quiz/stats"
                className="mt-3 block text-center text-sm text-(--tgui--link_color) no-underline"
              >
                Вся статистика угадывания
              </Link>
            </ProfileStatsSectionCard>
          ) : null}

          <ProfileStatsSectionCard title="Взаимные подписки">
            <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
              <p className="text-[10px] text-(--tgui--hint_color)">Люди, с которыми вы подписаны друг на друга</p>
              <p className="text-lg font-semibold tabular-nums">{mutualSubscriptionsCount}</p>
            </div>
          </ProfileStatsSectionCard>

          {watchSummaryRows.length > 0 ? (
            <ProfileStatsSummaryCard title="С кем смотрите" rows={watchSummaryRows} />
          ) : (
            <ProfileStatsSectionCard title="С кем смотрите">
              <p className="text-sm text-(--tgui--hint_color)">
                {cardsQuery.company === '' ? 'Пока нет данных' : 'Нет совпадающего среза среди этого профиля.'}
              </p>
            </ProfileStatsSectionCard>
          )}

          {moodSummaryRows.length > 0 ? (
            <ProfileStatsSummaryCard title="Эмоции после" rows={moodSummaryRows} />
          ) : (
            <ProfileStatsSectionCard title="Эмоции после">
              <p className="text-sm text-(--tgui--hint_color)">
                {cardsQuery.moodAfter === '' ? 'Пока нет данных' : 'Нет строки настроения, совпадающей с фильтром.'}
              </p>
            </ProfileStatsSectionCard>
          )}

          <ProfileStatsSectionCard title="Похожие профили">
            <SocialTastePeers peers={tastePeers} />
          </ProfileStatsSectionCard>
        </>
      ) : null}

      {statsSubTab === 'rankings' ? (
        <>
          {rankingsErr != null ? (
            <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">{rankingsErr}</p>
          ) : null}

          <ProfileStatsSectionCard title="Топ по оценке">
            {rankingsLoading ? <StatsRatedCardSkeleton /> : <StatsRatedCardRows items={topMoviesDisplay} />}
          </ProfileStatsSectionCard>

          <ProfileStatsSectionCard title="Самые низкие оценки">
            {rankingsLoading ? <StatsRatedCardSkeleton /> : <StatsRatedCardRows items={worstMoviesDisplay} />}
          </ProfileStatsSectionCard>

          {prioritizedPopularTags.length > 0 ? (
            <ProfileStatsSectionCard title="Популярные теги">
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
            </ProfileStatsSectionCard>
          ) : null}
        </>
      ) : null}

      {statsSubTab === 'collection' && showPassportCollection ? (
        <ProfilePassportPanel
          userId={userId}
          isOwnProfile={showTasteQuizTeaser}
          onMarathonDrill={onMarathonDrill}
        />
      ) : null}
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
