import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { getMyLatestMonthlyRecap, getMyMonthlyRecap } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, MonthlyRecap } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { StatsDonutChart } from '../components/profile/ProfileStatsCharts'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { COMPANY_OPTIONS, MOOD_AFTER_OPTIONS } from '../lib/cardFormOptions'
import {
  DECADE_DONUT_COLORS,
  GENRE_DONUT_COLORS,
  type DonutSegmentInput,
} from '../lib/statsDonutChart'

const MONTH_NAMES = [
  '',
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
]

function parseRouteMonth(raw: string | undefined): number | null {
  if (raw == null) return null
  const month = Number(raw)
  if (!Number.isInteger(month) || month < 1 || month > 12) return null
  return month
}

function parseRouteYear(raw: string | undefined): number | null {
  if (raw == null) return null
  const year = Number(raw)
  if (!Number.isInteger(year) || year < 2000 || year > 2100) return null
  return year
}

function formatPeakDate(iso: string | null): string | null {
  if (iso == null) return null
  const date = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

function filmsWord(count: number): string {
  if (count % 10 === 1 && count % 100 !== 11) return 'фильм'
  if (count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14)) return 'фильма'
  return 'фильмов'
}

function formatSignedDelta(value: number, fractionDigits = 0): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(fractionDigits)}`
}

function formatRecapAchievementRarity(rarityPercent: number | null): string {
  if (rarityPercent == null) return '—'
  return rarityPercent >= 0.1
    ? `${rarityPercent.toFixed(1)}%`
    : `${rarityPercent.toFixed(2)}%`
}

function companyLabel(value: CardCompany): string {
  return COMPANY_OPTIONS.find((option) => option.value === value)?.label ?? value
}

function moodAfterLabel(value: CardMoodAfter): string {
  return MOOD_AFTER_OPTIONS.find((option) => option.value === value)?.label ?? value
}

function marathonKindLabel(kind: string): string {
  return kind === 'director' ? 'Режиссёр' : 'Франшиза'
}

function marathonLinkTo(marathon: { kind: string; key: string }): string | null {
  if (marathon.kind === 'director') {
    const parsed = Number.parseInt(marathon.key, 10)
    if (Number.isInteger(parsed) && parsed >= 1) {
      return `/directors/${parsed}`
    }
    return null
  }
  if (marathon.kind === 'franchise') {
    const key = marathon.key.trim()
    if (key !== '') {
      return `/franchises/${encodeURIComponent(key)}`
    }
  }
  return null
}

export function MonthlyRecapPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const params = useParams()
  const year = parseRouteYear(params.year)
  const month = parseRouteMonth(params.month)

  const [recap, setRecap] = useState<MonthlyRecap | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (auth.kind !== 'ready') return
    let cancelled = false
    queueMicrotask(() => {
      setLoading(true)
      setError(null)
    })
    const load = year != null && month != null
      ? getMyMonthlyRecap(year, month)
      : getMyLatestMonthlyRecap()
    void load
      .then((data) => {
        if (!cancelled) setRecap(data)
      })
      .catch(() => {
        if (!cancelled) setError('Не удалось загрузить итоги месяца')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [auth.kind, year, month])

  const title = useMemo(() => {
    if (recap == null) return 'Итоги месяца'
    const label = MONTH_NAMES[recap.month] ?? String(recap.month)
    return `${label} ${recap.year}`
  }, [recap])

  const genreDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = recap?.genre_breakdown ?? []
    return rows
      .filter((item) => item.count > 0)
      .map((item, idx) => ({
        label: item.label,
        count: item.count,
        color: GENRE_DONUT_COLORS[idx % GENRE_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [recap?.genre_breakdown])

  const decadeDonutSegments = useMemo((): DonutSegmentInput[] => {
    const rows = recap?.decade_breakdown ?? []
    return rows
      .filter((item) => item.count > 0)
      .map((item, idx) => ({
        label: item.label,
        count: item.count,
        color: DECADE_DONUT_COLORS[idx % DECADE_DONUT_COLORS.length] ?? '#5de1d4',
      }))
  }, [recap?.decade_breakdown])

  if (auth.kind === 'loading' || auth.kind === 'skipped') {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (auth.kind === 'error') {
    return (
      <PageErrorState message={auth.message} backLabel="На главную" backHref="/" className="bg-(--tgui--bg_color)" />
    )
  }

  if (loading) {
    return <PageLoadingState message="Собираем итоги…" className="bg-(--tgui--bg_color)" />
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          ←
        </button>
        <h1 className="truncate text-base font-semibold">{title}</h1>
      </header>

      <main className="space-y-4 px-4 py-4">
        {error != null ? (
          <PageErrorState message={error} backLabel="Назад" backHref="/profile" />
        ) : null}
        {recap != null ? (
          <>
            <section className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Оценок</p>
                <p className="text-2xl font-semibold tabular-nums">{recap.total_rated}</p>
              </div>
              <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Средняя оценка</p>
                <p className="text-2xl font-semibold tabular-nums">{recap.average_rating.toFixed(1)}</p>
              </div>
            </section>

            {recap.vs_previous_total_rated != null ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">К прошлому месяцу</p>
                <p className="text-sm font-medium">
                  {formatSignedDelta(recap.vs_previous_total_rated)}{' '}
                  {filmsWord(Math.abs(recap.vs_previous_total_rated))}
                </p>
                {recap.vs_previous_average_rating != null ? (
                  <p className="mt-1 text-[11px] text-(--tgui--hint_color)">
                    Средняя оценка: {formatSignedDelta(recap.vs_previous_average_rating, 1)}
                  </p>
                ) : null}
              </section>
            ) : null}

            {recap.genre_of_month != null ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Жанр месяца</p>
                <p className="text-sm font-medium">
                  {recap.genre_of_month}
                  {(recap.genre_of_month_count ?? 0) > 0
                    ? ` · ${recap.genre_of_month_count ?? 0} ${(recap.genre_of_month_count ?? 0) === 1 ? 'фильм' : (recap.genre_of_month_count ?? 0) < 5 ? 'фильма' : 'фильмов'}`
                    : ''}
                </p>
              </section>
            ) : null}

            {recap.top_director_name != null && (recap.top_director_count ?? 0) > 0 ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Режиссёр месяца</p>
                <p className="text-sm font-medium">
                  {recap.top_director_kinopoisk_id != null ? (
                    <Link
                      to={`/directors/${recap.top_director_kinopoisk_id}`}
                      className="text-(--tgui--link_color) no-underline"
                    >
                      {recap.top_director_name}
                    </Link>
                  ) : (
                    recap.top_director_name
                  )}
                  {' · '}
                  {recap.top_director_count ?? 0}{' '}
                  {(recap.top_director_count ?? 0) === 1 ? 'фильм' : (recap.top_director_count ?? 0) < 5 ? 'фильма' : 'фильмов'}
                </p>
              </section>
            ) : null}

            {recap.top_country != null && (recap.top_country_count ?? 0) > 0 ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Страна месяца</p>
                <p className="text-sm font-medium">
                  {recap.top_country} · {recap.top_country_count ?? 0}{' '}
                  {(recap.top_country_count ?? 0) === 1 ? 'фильм' : (recap.top_country_count ?? 0) < 5 ? 'фильма' : 'фильмов'}
                </p>
                {(recap.new_countries_count ?? 0) > 0 ? (
                  <p className="mt-1 text-[11px] text-(--tgui--hint_color)">
                    🌍 Новых стран: {recap.new_countries_count}
                  </p>
                ) : null}
              </section>
            ) : null}

            {recap.top_actor_name != null && (recap.top_actor_count ?? 0) > 0 ? (
              <section className="space-y-2 rounded-xl border border-(--tgui--divider_color) p-3">
                <h2 className="text-sm font-semibold">Люди</h2>
                <div>
                  <p className="text-[11px] text-(--tgui--hint_color)">Актёр месяца</p>
                  <p className="text-sm font-medium">
                    {recap.top_actor_kinopoisk_id != null ? (
                      <Link
                        to={`/actors/${recap.top_actor_kinopoisk_id}`}
                        className="text-(--tgui--link_color) no-underline"
                      >
                        {recap.top_actor_name}
                      </Link>
                    ) : (
                      recap.top_actor_name
                    )}
                    {' · '}
                    {recap.top_actor_count ?? 0}{' '}
                    {filmsWord(recap.top_actor_count ?? 0)}
                  </p>
                </div>
                {(recap.actor_breakdown ?? []).length > 0 ? (
                  <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                    {recap.actor_breakdown?.map((actor) => (
                      <li key={actor.kinopoisk_id} className="flex items-center justify-between gap-3 px-3 py-2">
                        <Link
                          to={`/actors/${actor.kinopoisk_id}`}
                          className="min-w-0 truncate text-sm text-(--tgui--link_color) no-underline"
                        >
                          {actor.label}
                        </Link>
                        <span className="shrink-0 text-xs tabular-nums text-(--tgui--hint_color)">
                          {actor.count}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}

            {(recap.collection_deltas ?? []).length > 0 ? (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Коллекции</h2>
                <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                  {recap.collection_deltas?.map((item) => (
                    <li key={item.collection_slug} className="flex items-center justify-between gap-3 px-3 py-2.5">
                      <Link
                        to={`/collections/${encodeURIComponent(item.collection_slug)}`}
                        className="min-w-0 truncate text-sm text-(--tgui--link_color) no-underline"
                      >
                        {item.title}
                      </Link>
                      <span className="shrink-0 text-sm font-semibold tabular-nums text-(--tgui--link_color)">
                        +{item.films_rated_in_period}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {(recap.achievements_unlocked ?? []).length > 0 ? (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Достижения</h2>
                <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                  {recap.achievements_unlocked?.map((achievement) => (
                    <li key={achievement.slug} className="flex items-start justify-between gap-3 px-3 py-2.5">
                      <p className="min-w-0 text-sm font-medium">{achievement.title}</p>
                      <span className="shrink-0 text-xs font-medium tabular-nums text-(--tgui--link_color)">
                        {formatRecapAchievementRarity(achievement.rarity_percent)}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {(recap.streak_current ?? 0) > 0 || (recap.streak_best_in_period ?? 0) > 0 ? (
              <section className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3">
                  <p className="text-[11px] text-(--tgui--hint_color)">Текущая серия</p>
                  <p className="text-2xl font-semibold tabular-nums">{recap.streak_current ?? 0}</p>
                </div>
                <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3">
                  <p className="text-[11px] text-(--tgui--hint_color)">Лучшая за месяц</p>
                  <p className="text-2xl font-semibold tabular-nums">{recap.streak_best_in_period ?? 0}</p>
                </div>
              </section>
            ) : null}

            {recap.dominant_mood_after != null || recap.dominant_company != null ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Настроение и компания</p>
                {recap.dominant_mood_after != null ? (
                  <p className="text-sm font-medium">
                    После просмотра: {moodAfterLabel(recap.dominant_mood_after)}
                  </p>
                ) : null}
                {recap.dominant_company != null ? (
                  <p className={`text-sm font-medium${recap.dominant_mood_after != null ? ' mt-1' : ''}`}>
                    Компания: {companyLabel(recap.dominant_company)}
                  </p>
                ) : null}
              </section>
            ) : null}

            {genreDonutSegments.length > 0 ? (
              <section className="space-y-2 rounded-xl border border-(--tgui--divider_color) p-3">
                <h2 className="text-sm font-semibold">Жанры</h2>
                <StatsDonutChart segments={genreDonutSegments} centerTitle="оценок" legendCollapsedTopN={8} />
              </section>
            ) : null}

            {decadeDonutSegments.length > 0 ? (
              <section className="space-y-2 rounded-xl border border-(--tgui--divider_color) p-3">
                <h2 className="text-sm font-semibold">Десятилетия</h2>
                <StatsDonutChart segments={decadeDonutSegments} centerTitle="оценок" legendCollapsedTopN={8} />
              </section>
            ) : null}

            {recap.peak_activity_date != null && recap.peak_activity_count > 0 ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <p className="text-[11px] text-(--tgui--hint_color)">Пик активности</p>
                <p className="text-sm font-medium">
                  {formatPeakDate(recap.peak_activity_date)} — {recap.peak_activity_count}{' '}
                  {recap.peak_activity_count === 1 ? 'оценка' : 'оценки'}
                </p>
              </section>
            ) : null}

            {recap.top_films.length > 0 ? (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Топ месяца</h2>
                <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                  {recap.top_films.map((film) => (
                    <li key={film.card_id} className="flex items-center gap-3 px-3 py-2.5">
                      {film.poster_url != null ? (
                        <img
                          src={film.poster_url}
                          alt=""
                          className="size-10 rounded-md object-cover"
                        />
                      ) : (
                        <div className="flex size-10 items-center justify-center rounded-md bg-(--tgui--secondary_bg_color) text-[10px] text-(--tgui--hint_color)">
                          ?
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        {film.film_id != null ? (
                          <Link
                            to={`/films/${film.film_id}`}
                            className="block truncate text-sm text-(--tgui--link_color) no-underline"
                          >
                            {film.title}
                          </Link>
                        ) : (
                          <Link
                            to={`/cards/${film.card_id}`}
                            className="block truncate text-sm text-(--tgui--link_color) no-underline"
                          >
                            {film.title}
                          </Link>
                        )}
                      </div>
                      <span className="shrink-0 text-sm font-semibold tabular-nums text-(--tgui--link_color)">
                        {film.rating.toFixed(1)}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {recap.new_stamps.length > 0 ? (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Новые штампы</h2>
                <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                  {recap.new_stamps.map((stamp) => (
                    <li key={stamp.stamp_id} className="px-3 py-2 text-sm">
                      {stamp.title}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {recap.marathons_unlocked.length > 0 ? (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Марафоны</h2>
                <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
                  {recap.marathons_unlocked.map((marathon) => {
                    const to = marathonLinkTo(marathon)
                    return (
                      <li key={`${marathon.kind}:${marathon.key}`} className="px-3 py-2.5">
                        <p className="text-[11px] text-(--tgui--hint_color)">{marathonKindLabel(marathon.kind)}</p>
                        <p className="text-sm font-medium">
                          {to != null ? (
                            <Link to={to} className="text-(--tgui--link_color) no-underline">
                              {marathon.label}
                            </Link>
                          ) : (
                            marathon.label
                          )}
                        </p>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ) : null}

            {(recap.fun_facts?.length ?? 0) > 0 ? (
              <section className="rounded-xl border border-(--tgui--divider_color) p-3">
                <h2 className="mb-3 text-sm font-semibold">Приколы месяца</h2>
                {recap.fun_facts?.map((fact) => (
                  <p key={fact} className="text-sm">{fact}</p>
                ))}
              </section>
            ) : null}

            {recap.total_rated === 0 ? (
              <p className="text-sm text-(--tgui--hint_color)">
                В этом месяце не было оценок — загляни в другой период из профиля.
              </p>
            ) : null}
          </>
        ) : null}
      </main>
    </div>
  )
}
