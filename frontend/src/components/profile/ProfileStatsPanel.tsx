import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../../api/client'
import { getUserMovieCardStats } from '../../api/profileApi'
import type { ProfileStatsMovieItem, UserMovieCardStats } from '../../api/profileTypes'

type ProfileStatsPanelProps = {
  userId: string
}

const COMPANY_LABELS: Record<string, string> = {
  alone: 'Один',
  partner: 'С партнером',
  friends: 'С друзьями',
  family: 'С семьей',
}

const MOOD_AFTER_LABELS: Record<string, string> = {
  laughed: 'Смеялся',
  cried: 'Плакал',
  enjoyed: 'Кайфанул',
  tense: 'Уставший',
  wasted_time: 'Зря потратил время',
}

function formatRating(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function ColumnChart({
  items,
  maxCount,
}: {
  items: Array<{ label: string; count: number }>
  maxCount: number
}) {
  return (
    <div className="overflow-x-auto pb-1">
      <div className="flex min-h-48 min-w-max items-end gap-3">
        {items.map((item) => {
          const rawHeight = maxCount > 0 ? (item.count / maxCount) * 100 : 0
          const barHeight = item.count > 0 ? Math.max(rawHeight, 8) : 0
          return (
            <div key={item.label} className="flex w-9 shrink-0 flex-col items-center gap-2">
              <span className="text-xs tabular-nums text-(--tgui--hint_color)">{item.count}</span>
              <div className="flex h-32 w-full items-end rounded-xl bg-(--tgui--bg_color) p-1">
                <div
                  className="w-full rounded-lg bg-[linear-gradient(180deg,#72efe4_0%,#52d6c7_100%)]"
                  style={{ height: `${barHeight}%` }}
                />
              </div>
              <span className="text-sm tabular-nums text-(--tgui--hint_color)">{item.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function MovieList({ items }: { items: ProfileStatsMovieItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <ul className="divide-y divide-(--tgui--divider_color)">
        {items.map((movie) => (
          <li key={movie.card_id}>
            <Link
              to={`/cards/${movie.card_id}`}
              className="flex items-center justify-between gap-3 px-3 py-3 text-sm no-underline outline-none transition-[background-color,transform] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] active:scale-[0.998] focus-visible:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)"
            >
              <div className="min-w-0">
                <p className="truncate text-(--tgui--text_color)">{movie.film_title}</p>
                <p className="text-xs text-(--tgui--hint_color)">{movie.film_year ?? 'Год неизвестен'}</p>
              </div>
              <span className="shrink-0 text-lg font-semibold tabular-nums text-(--tgui--link_color)">
                {formatRating(movie.rating)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function ProfileStatsPanel({ userId }: ProfileStatsPanelProps) {
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

  const ratingMax = useMemo(
    () => Math.max(0, ...(stats?.rating_distribution.map((item) => item.count) ?? [0])),
    [stats],
  )
  const yearMax = useMemo(
    () => Math.max(0, ...(stats?.year_distribution.map((item) => item.count) ?? [0])),
    [stats],
  )
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
    return { low, mid, high, total, lowPct, midPct, highPct }
  }, [stats])

  if (loading && stats == null) {
    return <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка статистики…</p>
  }
  if (error != null) {
    return <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
  }
  if (stats == null) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
          <p className="text-xs text-(--tgui--hint_color)">Всего карточек</p>
          <p className="mt-1 text-4xl font-bold tabular-nums">{stats.total_movies}</p>
        </div>
        <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
          <p className="text-xs text-(--tgui--hint_color)">Средняя оценка</p>
          <p className="mt-1 text-4xl font-bold tabular-nums">{formatRating(stats.average_rating)}</p>
        </div>
      </div>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">Распределение оценок</p>
        <div className="mt-3">
          {stats.rating_distribution.some((item) => item.count > 0) ? (
            <ColumnChart
              items={stats.rating_distribution.map((item) => ({
                label: String(item.rating),
                count: item.count,
              }))}
              maxCount={ratingMax}
            />
          ) : (
            <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">По годам выпуска</p>
        <div className="mt-3">
          {stats.year_distribution.length > 0 ? (
            <ColumnChart
              items={stats.year_distribution.map((item) => ({
                label: String(item.year),
                count: item.count,
              }))}
              maxCount={yearMax}
            />
          ) : (
            <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">Полярность вкуса</p>
        {sentiment.total > 0 ? (
          <div className="mt-3 flex items-center gap-4">
            <div
              className="relative h-28 w-28 shrink-0 rounded-full"
              style={{
                background: `conic-gradient(#5de1d4 0% ${sentiment.highPct}%, #4f87ff ${sentiment.highPct}% ${
                  sentiment.highPct + sentiment.midPct
                }%, #ef7d9b ${sentiment.highPct + sentiment.midPct}% 100%)`,
              }}
            >
              <div className="absolute inset-3 flex items-center justify-center rounded-full bg-(--tgui--secondary_bg_color) text-center">
                <div>
                  <p className="text-[10px] text-(--tgui--hint_color)">оценок</p>
                  <p className="text-lg font-bold tabular-nums">{sentiment.total}</p>
                </div>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <p className="flex items-center gap-2">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#5de1d4]" />
                Высокие (8-10): {sentiment.high} ({sentiment.highPct}%)
              </p>
              <p className="flex items-center gap-2">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#4f87ff]" />
                Средние (5-7): {sentiment.mid} ({sentiment.midPct}%)
              </p>
              <p className="flex items-center gap-2">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#ef7d9b]" />
                Низкие (1-4): {sentiment.low} ({sentiment.lowPct}%)
              </p>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-(--tgui--hint_color)">Пока нет данных</p>
        )}
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">Популярные теги</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {stats.popular_tags.length > 0 ? (
            stats.popular_tags.map((tag) => (
              <span
                key={tag.tag}
                className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1 text-xs"
              >
                {tag.tag} ({tag.count})
              </span>
            ))
          ) : (
            <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">С кем смотрю</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {stats.watch_with_distribution.length > 0 ? (
            stats.watch_with_distribution.map((item) => (
              <span
                key={item.value}
                className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1 text-xs"
              >
                {COMPANY_LABELS[item.value] ?? item.value} ({item.count})
              </span>
            ))
          ) : (
            <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="text-sm font-medium">Настроение после просмотра</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {stats.mood_after_distribution.length > 0 ? (
            stats.mood_after_distribution.map((item) => (
              <span
                key={item.value}
                className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1 text-xs"
              >
                {MOOD_AFTER_LABELS[item.value] ?? item.value} ({item.count})
              </span>
            ))
          ) : (
            <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="mb-3 text-sm font-medium">Топ по оценке</p>
        <MovieList items={stats.top_movies} />
      </section>

      <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
        <p className="mb-3 text-sm font-medium">Самые низкие оценки</p>
        <MovieList items={stats.worst_movies} />
      </section>
    </div>
  )
}
