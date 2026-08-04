import { Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { ChevronLeft } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router'

import { getFranchiseFilmsPage, getFranchiseSummary } from '../api/franchisesApi'
import { ApiError, formatApiDetail } from '../api/client'
import { useAuthStatus } from '../auth/useAuthStatus'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { formatRating } from '../components/feed/feedCardUtils'
import { franchiseChipStyles } from '../lib/franchiseColor'

function franchiseSummaryQueryKey(franchiseKey: string) {
  return ['franchiseSummary', franchiseKey] as const
}

function franchiseFilmsQueryKey(franchiseKey: string) {
  return ['franchiseFilms', franchiseKey] as const
}

export function FranchiseDetailPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { franchiseKey: rawKey } = useParams<{ franchiseKey: string }>()
  const franchiseKey = rawKey?.trim() ?? ''

  const summaryQuery = useQuery({
    queryKey: franchiseSummaryQueryKey(franchiseKey),
    queryFn: () => getFranchiseSummary(franchiseKey),
    enabled: auth.kind === 'ready' && franchiseKey !== '',
    staleTime: 60_000,
  })

  const filmsQuery = useInfiniteQuery({
    queryKey: franchiseFilmsQueryKey(franchiseKey),
    queryFn: ({ pageParam }) =>
      getFranchiseFilmsPage(franchiseKey, {
        cursor: pageParam ?? null,
        limit: 20,
      }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: auth.kind === 'ready' && franchiseKey !== '' && summaryQuery.isSuccess,
    staleTime: 45_000,
  })

  const summary = summaryQuery.data
  const films = filmsQuery.data?.pages.flatMap((page) => page.items) ?? []
  const accent = franchiseKey !== '' ? franchiseChipStyles(franchiseKey) : null

  if (auth.kind === 'loading' || auth.kind === 'skipped') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        Вход…
      </div>
    )
  }

  if (franchiseKey === '') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-12 text-center text-sm text-(--tgui--hint_color)">
        Некорректная ссылка на франшизу
      </div>
    )
  }

  const summaryErr =
    summaryQuery.error instanceof ApiError
      ? formatApiDetail(summaryQuery.error.detail)
      : summaryQuery.error != null
        ? 'Не удалось загрузить франшизу'
        : null

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-8 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex size-9 items-center justify-center rounded-full text-(--tgui--text_color) outline-none active:opacity-80"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          <ChevronLeft className="block size-5" strokeWidth={1.75} aria-hidden />
        </button>
        <span className="truncate text-sm font-medium">Франшиза</span>
      </header>

      <main className="mx-auto max-w-md space-y-4 px-4 pt-4">
        {summaryQuery.isPending ? (
          <p className="filmony-text-panel py-12 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {summaryErr != null ? (
          <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-4">
            <p className="text-sm text-(--tgui--destructive_text_color)">{summaryErr}</p>
          </div>
        ) : null}

        {summary != null && accent != null ? (
          <>
            <div
              className={`rounded-2xl border px-4 py-4 ${accent.borderClass} ${accent.backgroundClass}`}
            >
              <Title level="2" weight="2">
                {summary.label}
              </Title>
              <div className="mt-3 flex flex-wrap gap-3 text-sm tabular-nums text-(--tgui--hint_color)">
                <span>
                  <span className="font-semibold text-(--tgui--text_color)">{summary.films_count}</span> фильмов с
                  оценками
                </span>
                {summary.avg_community_rating != null ? (
                  <span>
                    средняя{' '}
                    <span className="font-semibold text-(--tgui--text_color)">
                      {formatRating(summary.avg_community_rating)}
                    </span>
                  </span>
                ) : null}
              </div>
            </div>

            <Section header="Фильмы в Filmony">
              {films.length === 0 && !filmsQuery.isPending ? (
                <p className="px-3 py-4 text-sm text-(--tgui--hint_color)">
                  Пока нет оценённых фильмов этой франшизы
                </p>
              ) : (
                <ul className="divide-y divide-(--tgui--divider_color)">
                  {films.map((film) => (
                    <li key={film.film_id}>
                      <Link
                        to={`/films/${film.film_id}`}
                        className="flex gap-3 px-3 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)"
                      >
                        <div className="h-[4.5rem] w-12 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                          {film.poster_url ? (
                            <img
                              src={film.poster_url}
                              alt=""
                              className="h-full w-full object-cover"
                              loading="lazy"
                              decoding="async"
                            />
                          ) : null}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-2 text-sm font-medium text-(--tgui--text_color)">{film.title}</p>
                          <p className="mt-0.5 text-xs text-(--tgui--hint_color)">{film.year ?? '—'}</p>
                          <FilmGenreChips genres={film.genres} maxVisible={2} className="mt-1.5" />
                          <p className="mt-1 text-xs tabular-nums text-(--tgui--hint_color)">
                            {film.community_avg_rating != null ? (
                              <>
                                <span className="font-semibold text-(--tgui--text_color)">
                                  {formatRating(film.community_avg_rating)}
                                </span>
                                {' · '}
                              </>
                            ) : null}
                            {film.ratings_count}{' '}
                            {film.ratings_count === 1
                              ? 'оценка'
                              : film.ratings_count < 5
                                ? 'оценки'
                                : 'оценок'}
                          </p>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}

              {filmsQuery.hasNextPage ? (
                <div className="px-3 py-3">
                  <Button
                    stretched
                    mode="bezeled"
                    disabled={filmsQuery.isFetchingNextPage}
                    onClick={() => void filmsQuery.fetchNextPage()}
                  >
                    {filmsQuery.isFetchingNextPage ? 'Подгружаем…' : 'Подгрузить ещё'}
                  </Button>
                </div>
              ) : null}
            </Section>
          </>
        ) : null}
      </main>
    </div>
  )
}
