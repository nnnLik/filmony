import { Avatar } from '@telegram-apps/telegram-ui'
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
  RatingContrastInsights,
  TagDistributionItem,
  TagTasteItem,
  UserMovieCardStats,
} from '../../api/profileTypes'
import { profileStatsMoviePrimaryTitle } from '../../lib/movieCardDisplay'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'
import { mergeShelfDistributionWithMetadata } from '../../lib/profileShelfDistribution'
import {
  aggregateYearDistributionToDecades,
  COMPANY_DONUT_COLORS,
  DECADE_DONUT_COLORS,
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
import { ProfileStatsMetricStrip, ProfileStatsSectionCard } from './ProfileStatsSummaryCard'
import { TasteQuizKnowledgeList } from '../tasteQuiz/TasteQuizKnowledgeList'
import { TabEmptyState } from '../ui/TabEmptyState'
import { listTasteQuizKnowledge } from '../../api/tasteQuizApi'
import type { TasteQuizKnowledgeItem } from '../../api/tasteQuizTypes'
import type { MarathonAchievement } from '../../api/gamificationTypes'
import { publicProfileCardCategoriesQueryKey } from '../../feed/feedQueryKeys'
import { profileStatsFilteredRankingsQueryKey } from '../../lib/profileQueryKeys'
import { useUserMovieCardStatsQuery } from '../../hooks/useUserMovieCardStatsQuery'
import { ProfilePassportPanel } from './gamification/ProfilePassportPanel'
import { AchievementsPanel } from './AchievementsPanel'
import { SegmentedControl } from '../ui/SegmentedControl'

type StatsSubTab = 'overview' | 'taste' | 'social' | 'rankings' | 'rewards'
type PeopleKind = 'directors' | 'actors'

const BASE_STATS_SUB_TABS: { id: StatsSubTab; label: string }[] = [
  { id: 'overview', label: 'Обзор' },
  { id: 'taste', label: 'Вкус' },
  { id: 'social', label: 'Социальность' },
  { id: 'rankings', label: 'Рейтинги' },
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
  /** Управление достижениями и закреплениями (только свой профиль). */
  showAchievements?: boolean
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

function personInitials(name: string): string {
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

function distributionFilmsLabel(count: number): string {
  return `${count} ${count === 1 ? 'фильм' : count < 5 ? 'фильма' : 'фильмов'}`
}

type PersonDistributionStripItem = {
  kinopoisk_id: number
  name: string
  count: number
  poster_url?: string | null
}

function personPosterSrc(posterUrl: string | null | undefined): string | undefined {
  const trimmed = posterUrl?.trim()
  if (trimmed == null || trimmed === '') return undefined
  return resolveApiMediaUrl(trimmed) ?? trimmed
}

function PersonDistributionStrip({
  items,
  userId,
  personKind,
}: {
  items: PersonDistributionStripItem[]
  userId: string
  personKind: 'directors' | 'actors'
}) {
  const visible = items.filter((item) => item.count > 0)
  if (visible.length === 0) return null

  return (
    <div
      className="-mx-1 flex snap-x snap-mandatory gap-2.5 overflow-x-auto scroll-px-2 px-1 pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="list"
    >
      {visible.map((item) => {
        const href =
          userId !== ''
            ? `/${personKind}/${item.kinopoisk_id}?userId=${encodeURIComponent(userId)}`
            : `/${personKind}/${item.kinopoisk_id}`
        return (
          <Link
            key={item.kinopoisk_id}
            to={href}
            role="listitem"
            className="group flex w-[4.75rem] shrink-0 snap-start flex-col items-center gap-1.5 rounded-xl px-1 py-1 no-underline text-(--tgui--text_color) transition-[background,transform] duration-200 ease-out active:scale-[0.98] hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_08%,transparent)]"
          >
            <div className="relative flex size-[52px] shrink-0 items-center justify-center rounded-full bg-(--tgui--bg_color) shadow-[0_0_0_1px_color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] transition-shadow duration-200 group-hover:shadow-[0_0_0_2px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)]">
              <Avatar
                size={48}
                src={personPosterSrc(item.poster_url)}
                acronym={personInitials(item.name)}
              />
            </div>
            <span className="line-clamp-2 w-full text-center text-[11px] font-medium leading-tight">
              {item.name}
            </span>
            <span className="line-clamp-2 w-full text-center text-[10px] leading-tight text-(--tgui--hint_color)">
              {distributionFilmsLabel(item.count)}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

function PeopleDistributionSection({
  stats,
  userId,
}: {
  stats: UserMovieCardStats
  userId: string
}) {
  const directors = stats.director_distribution ?? []
  const actors = stats.actor_distribution ?? []
  const hasDirectors = directors.some((director) => director.count > 0)
  const hasActors = actors.some((actor) => actor.count > 0)
  const [peopleKindOverride, setPeopleKindOverride] = useState<PeopleKind | null>(null)
  const peopleKind: PeopleKind =
    peopleKindOverride ?? (hasDirectors ? 'directors' : 'actors')

  if (!hasDirectors && !hasActors) {
    return (
      <ProfileStatsSectionCard title="Люди">
        <div className="space-y-3">
          <p className="text-sm text-(--tgui--hint_color)">
            Режиссёры и актёры появятся, когда в карточках будут фильмы с метаданными Кинопоиска.
          </p>
          <TabEmptyState
            fallback="Оцените фильм — мы построим распределение по режиссёрам и актёрам."
            userId={userId}
            action={{ label: 'Добавить карточку', href: '/cards/new' }}
            className="py-4"
          />
        </div>
      </ProfileStatsSectionCard>
    )
  }

  const showToggle = hasDirectors && hasActors
  const topDirectorId = stats.insights?.top_director_kinopoisk_id
  const topActorId = stats.insights?.top_actor_kinopoisk_id

  return (
    <ProfileStatsSectionCard title="Люди">
      <div className="space-y-3">
        {showToggle ? (
          <SegmentedControl
            value={peopleKind}
            onChange={setPeopleKindOverride}
            segments={[
              { value: 'directors', label: 'Режиссёры', disabled: !hasDirectors },
              { value: 'actors', label: 'Актёры', disabled: !hasActors },
            ]}
            ariaLabel="Режиссёры или актёры"
            size="sm"
          />
        ) : null}

        {peopleKind === 'directors' && hasDirectors ? (
          <>
            <PersonDistributionStrip items={directors} userId={userId} personKind="directors" />
            {topDirectorId != null ? (
              <Link
                to={`/directors/${topDirectorId}${userId !== '' ? `?userId=${encodeURIComponent(userId)}` : ''}`}
                className="block text-center text-sm text-(--tgui--link_color) no-underline"
              >
                Страница топ-режиссёра →
              </Link>
            ) : null}
          </>
        ) : null}

        {peopleKind === 'actors' && hasActors ? (
          <>
            <PersonDistributionStrip items={actors} userId={userId} personKind="actors" />
            {topActorId != null ? (
              <Link
                to={`/actors/${topActorId}${userId !== '' ? `?userId=${encodeURIComponent(userId)}` : ''}`}
                className="block text-center text-sm text-(--tgui--link_color) no-underline"
              >
                Страница топ-актёра →
              </Link>
            ) : null}
          </>
        ) : null}
      </div>
    </ProfileStatsSectionCard>
  )
}

function formatRating(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatSignedDelta(value: number | null | undefined): string | null {
  if (value == null || !Number.isFinite(value)) return null
  const rounded = Math.round(value * 10) / 10
  const formatted = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1)
  if (rounded > 0) return `+${formatted}`
  return formatted
}

function hasRatingContrastData(contrast: RatingContrastInsights | undefined): contrast is RatingContrastInsights {
  if (contrast == null) return false
  return (
    contrast.avg_delta_kinopoisk != null ||
    contrast.avg_delta_imdb != null ||
    contrast.biggest_gap != null ||
    contrast.agreement_percent > 0 ||
    contrast.contrarian_count > 0
  )
}

function ratingContrastBiggestGapLink(contrast: RatingContrastInsights): string | undefined {
  const gap = contrast.biggest_gap
  if (gap == null) return undefined
  if (gap.film_id != null && gap.film_id > 0) {
    return `/films/${gap.film_id}`
  }
  if (gap.card_id > 0) {
    return `/cards/${gap.card_id}`
  }
  return undefined
}

function RatingContrastSection({ contrast }: { contrast: RatingContrastInsights }) {
  const avgKp = formatSignedDelta(contrast.avg_delta_kinopoisk)
  const avgImdb = formatSignedDelta(contrast.avg_delta_imdb)
  const biggestGap = contrast.biggest_gap
  const biggestGapLink = ratingContrastBiggestGapLink(contrast)

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {avgKp != null ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
          <p className="text-[10px] text-(--tgui--hint_color)">Средняя дельта КП</p>
          <p className="text-lg font-semibold tabular-nums">{avgKp}</p>
        </div>
      ) : null}
      {avgImdb != null ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
          <p className="text-[10px] text-(--tgui--hint_color)">Средняя дельта IMDb</p>
          <p className="text-lg font-semibold tabular-nums">{avgImdb}</p>
        </div>
      ) : null}
      <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
        <p className="text-[10px] text-(--tgui--hint_color)">Совпадение с агрегаторами</p>
        <p className="text-lg font-semibold tabular-nums">{Math.round(contrast.agreement_percent)}%</p>
      </div>
      <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2">
        <p className="text-[10px] text-(--tgui--hint_color)">Контр-культ</p>
        <p className="text-lg font-semibold tabular-nums">{contrast.contrarian_count}</p>
      </div>
      {biggestGap != null ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2 sm:col-span-2">
          <p className="text-[10px] text-(--tgui--hint_color)">Самый большой разрыв</p>
          {biggestGapLink != null ? (
            <Link to={biggestGapLink} className="mt-0.5 block truncate text-sm font-medium text-(--tgui--link_color) no-underline">
              {biggestGap.film_title}
            </Link>
          ) : (
            <p className="mt-0.5 truncate text-sm font-medium">{biggestGap.film_title}</p>
          )}
          <p className="mt-0.5 text-xs tabular-nums text-(--tgui--hint_color)">Δ {formatSignedDelta(biggestGap.gap) ?? '—'}</p>
        </div>
      ) : null}
    </div>
  )
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
  userId: string,
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
        to:
          snap.top_director_kinopoisk_id != null && snap.top_director_kinopoisk_id > 0
            ? userId !== ''
              ? `/directors/${snap.top_director_kinopoisk_id}?userId=${encodeURIComponent(userId)}`
              : `/directors/${snap.top_director_kinopoisk_id}`
            : undefined,
      })
    }
    if (snap.top_actor_name != null && snap.top_actor_name !== '') {
      items.push({
        key: 'top_actor',
        label: 'Любимый актёр',
        value: snap.top_actor_name,
        hint:
          snap.top_actor_count != null && snap.top_actor_count > 0
            ? `${snap.top_actor_count} ${snap.top_actor_count === 1 ? 'фильм' : snap.top_actor_count < 5 ? 'фильма' : 'фильмов'}`
            : undefined,
        to:
          snap.top_actor_kinopoisk_id != null && snap.top_actor_kinopoisk_id > 0
            ? userId !== ''
              ? `/actors/${snap.top_actor_kinopoisk_id}?userId=${encodeURIComponent(userId)}`
              : `/actors/${snap.top_actor_kinopoisk_id}`
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
  const contrast = stats.rating_contrast
  if (hasRatingContrastData(contrast)) {
    items.push({
      key: 'rating_agreement',
      label: 'Совпадение с КП/IMDb',
      value: `${Math.round(contrast.agreement_percent)}%`,
    })
    const avgKp = formatSignedDelta(contrast.avg_delta_kinopoisk)
    if (avgKp != null) {
      items.push({
        key: 'avg_delta_kp',
        label: 'Средняя дельта КП',
        value: avgKp,
      })
    }
    if (contrast.contrarian_count > 0) {
      items.push({
        key: 'contrarian_count',
        label: 'Контр-культ',
        value: String(contrast.contrarian_count),
        hint: 'оценок с разрывом ≥4',
      })
    }
    const biggestGapLink = ratingContrastBiggestGapLink(contrast)
    if (contrast.biggest_gap != null) {
      items.push({
        key: 'biggest_gap',
        label: 'Макс. разрыв',
        value: contrast.biggest_gap.film_title,
        hint: formatSignedDelta(contrast.biggest_gap.gap) != null
          ? `Δ ${formatSignedDelta(contrast.biggest_gap.gap)}`
          : undefined,
        to: biggestGapLink,
      })
    }
  }
  return items.slice(0, 4)
}

function StatsSubTabBar({
  active,
  onChange,
  tabs,
}: {
  active: StatsSubTab
  onChange: (tab: StatsSubTab) => void
  tabs: { id: StatsSubTab; label: string }[]
}) {
  return (
    <div
      className="flex gap-1 overflow-x-auto rounded-full bg-(--tgui--secondary_bg_color) p-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="tablist"
      aria-label="Разделы статистики"
    >
      {tabs.map((tab) => (
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
  showAchievements = false,
  onMarathonDrill,
}: ProfileStatsPanelProps) {
  const statsSubTabs = useMemo(() => {
    const tabs = [...BASE_STATS_SUB_TABS]
    if (showAchievements || showPassportCollection) {
      tabs.push({ id: 'rewards', label: 'Награды' })
    }
    return tabs
  }, [showAchievements, showPassportCollection])
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
    return [
      { label: 'Карточек', value: total },
      { label: 'Средний балл', value: avg },
    ]
  }, [stats])

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
      actorKinopoiskId: '',
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
      actorKinopoiskId: '',
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
    () => (stats != null ? deriveInsights(stats, sentiment, userId) : []),
    [stats, sentiment, userId],
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
      <StatsSubTabBar active={statsSubTab} onChange={setStatsSubTab} tabs={statsSubTabs} />

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

          {hasRatingContrastData(stats.rating_contrast) ? (
            <ProfileStatsSectionCard title="Оценки vs КП и IMDb">
              <RatingContrastSection contrast={stats.rating_contrast} />
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

          <PeopleDistributionSection stats={stats} userId={userId} />

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

      {statsSubTab === 'rewards' ? (
        <>
          {showPassportCollection ? (
            <ProfilePassportPanel
              userId={userId}
              isOwnProfile={showTasteQuizTeaser}
              onMarathonDrill={onMarathonDrill}
            />
          ) : null}
          {showAchievements ? <AchievementsPanel /> : null}
        </>
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
