import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'

import { getMyLatestWeeklyDigest, getMyWeeklyDigest } from '../api/profileApi'
import type { PersonalDigest } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'

function parsePeriodKey(raw: string | undefined): string | null {
  if (raw == null || raw === 'latest') return null
  const trimmed = raw.trim()
  if (!/^\d{4}-W\d{2}$/i.test(trimmed)) return null
  return trimmed.toUpperCase().replace(/-W(\d+)/, (_, week) => `-W${week}`)
}

function formatPeakDate(iso: string | null): string | null {
  if (iso == null) return null
  const date = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

export function WeeklyDigestPage() {
  const auth = useAuthStatus()
  const params = useParams()
  const periodKey = parsePeriodKey(params.periodKey)

  const [digest, setDigest] = useState<PersonalDigest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (auth.kind !== 'ready') return
    let cancelled = false
    queueMicrotask(() => {
      setLoading(true)
      setError(null)
    })
    const load = periodKey != null
      ? getMyWeeklyDigest(periodKey)
      : getMyLatestWeeklyDigest()
    void load
      .then((data) => {
        if (!cancelled) setDigest(data)
      })
      .catch(() => {
        if (!cancelled) setError('Не удалось загрузить сводку недели')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [auth.kind, periodKey])

  const title = useMemo(() => {
    if (digest == null) return 'Сводка недели'
    return `Твоя неделя · ${digest.period_label}`
  }, [digest])

  if (auth.kind === 'loading' || loading) {
    return <PageLoadingState />
  }

  if (error != null) {
    return <PageErrorState message={error} onRetry={() => { window.location.reload() }} />
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-4">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">{title}</h1>
        {digest?.period_key != null ? (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">{digest.period_key}</p>
        ) : null}
      </header>

      {digest != null ? (
        <>
          <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
              Обзор
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-[var(--tg-theme-hint-color)]">Оценок</p>
                <p className="text-2xl font-semibold tabular-nums">{digest.total_rated}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--tg-theme-hint-color)]">Средняя</p>
                <p className="text-2xl font-semibold tabular-nums">{digest.average_rating.toFixed(1)}</p>
              </div>
            </div>
            {digest.vs_previous_total_rated != null ? (
              <p className="mt-2 text-sm text-[var(--tg-theme-hint-color)]">
                {digest.vs_previous_total_rated > 0 ? '+' : ''}
                {digest.vs_previous_total_rated} к прошлой неделе
              </p>
            ) : null}
          </section>

          {digest.all_films != null && digest.all_films.length > 0 ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Фильмы
              </h2>
              <ul className="flex flex-col gap-2">
                {digest.all_films.map((film) => (
                  <li key={film.card_id} className="flex items-center justify-between gap-2">
                    <Link
                      to={`/cards/${film.card_id}`}
                      className="truncate font-medium text-[var(--tg-theme-link-color)]"
                    >
                      {film.title}
                    </Link>
                    <span className="tabular-nums font-semibold">{film.rating.toFixed(1)}</span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {digest.top_director_name != null && (digest.top_director_count ?? 0) > 0 ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Люди
              </h2>
              <p className="text-sm">
                🎬{' '}
                {digest.top_director_kinopoisk_id != null ? (
                  <Link
                    to={`/directors/${digest.top_director_kinopoisk_id}`}
                    className="font-medium text-[var(--tg-theme-link-color)]"
                  >
                    {digest.top_director_name}
                  </Link>
                ) : (
                  digest.top_director_name
                )}
                · {digest.top_director_count ?? 0}
              </p>
              {digest.top_actor_name != null && (digest.top_actor_count ?? 0) > 0 ? (
                <p className="mt-2 text-sm">
                  🎭{' '}
                  {digest.top_actor_kinopoisk_id != null ? (
                    <Link
                      to={`/actors/${digest.top_actor_kinopoisk_id}`}
                      className="font-medium text-[var(--tg-theme-link-color)]"
                    >
                      {digest.top_actor_name}
                    </Link>
                  ) : (
                    digest.top_actor_name
                  )}
                  · {digest.top_actor_count ?? 0}
                </p>
              ) : null}
            </section>
          ) : null}

          {digest.genre_of_month != null ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Вкус
              </h2>
              <p className="text-sm">Жанр: {digest.genre_of_month}</p>
              {digest.dominant_mood_after != null ? (
                <p className="mt-1 text-sm text-[var(--tg-theme-hint-color)]">
                  Настроение: {digest.dominant_mood_after}
                </p>
              ) : null}
              {digest.dominant_company != null ? (
                <p className="mt-1 text-sm text-[var(--tg-theme-hint-color)]">
                  Компания: {digest.dominant_company}
                </p>
              ) : null}
            </section>
          ) : null}

          {(digest.collection_deltas?.length ?? 0) > 0 || (digest.achievements_unlocked?.length ?? 0) > 0 ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Коллекции и ачивки
              </h2>
              {digest.collection_deltas?.map((item) => (
                <p key={item.collection_slug} className="text-sm">
                  {item.title} +{item.films_rated_in_period}
                </p>
              ))}
              {digest.achievements_unlocked?.map((item) => (
                <p key={item.slug} className="text-sm">🏆 {item.title}</p>
              ))}
            </section>
          ) : null}

          {digest.friends != null && digest.friends.in_app_items.length > 0 ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Друзья
              </h2>
              <ul className="flex flex-col gap-2">
                {digest.friends.in_app_items.map((item) => (
                  <li key={`${item.author_user_id}-${item.line_text}`} className="text-sm">
                    {item.profile_slug != null ? (
                      <Link
                        to={`/u/${item.profile_slug}`}
                        className="font-medium text-[var(--tg-theme-link-color)]"
                      >
                        {item.author_display}
                      </Link>
                    ) : (
                      <span className="font-medium">{item.author_display}</span>
                    )}
                    {' — '}
                    {item.line_text}
                  </li>
                ))}
              </ul>
              <Link to="/feed" className="mt-3 text-sm text-[var(--tg-theme-link-color)]">
                Вся активность подписок
              </Link>
            </section>
          ) : null}

          {(digest.fun_facts?.length ?? 0) > 0 ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Приколы недели
              </h2>
              {digest.fun_facts?.map((fact) => (
                <p key={fact} className="text-sm">{fact}</p>
              ))}
            </section>
          ) : null}

          {digest.controversy != null ? (
            <section className="rounded-2xl border border-[var(--tg-theme-section-separator-color)] p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--tg-theme-hint-color)]">
                Controversy
              </h2>
              <p className="text-sm">
                ⚡ Сильнее всего разошлись с {digest.controversy.friend_display} по «
                {digest.controversy.anchor_film_id != null ? (
                  <Link
                    to={`/films/${digest.controversy.anchor_film_id}`}
                    className="text-[var(--tg-theme-link-color)]"
                  >
                    {digest.controversy.film_title}
                  </Link>
                ) : (
                  digest.controversy.film_title
                )}
                »
              </p>
            </section>
          ) : null}

          {digest.peak_activity_date != null && digest.peak_activity_count > 0 ? (
            <p className="text-sm text-[var(--tg-theme-hint-color)]">
              Пик: {formatPeakDate(digest.peak_activity_date)} — {digest.peak_activity_count} оценки
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
