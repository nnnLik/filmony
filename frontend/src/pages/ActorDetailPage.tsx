import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router'

import { getActorFilmsPage, getActorSummary } from '../api/actorsApi'
import { CatalogEntitySummaryCard } from '../components/catalog/CatalogEntitySummaryCard'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { DetailPageSkeleton } from '../components/ui/DetailPageSkeleton'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { formatRating } from '../components/feed/feedCardUtils'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useEntitySummaryFilmsPage } from '../hooks/useEntitySummaryFilmsPage'
import { directorChipStyles } from '../lib/directorColor'
import { formatQueryError } from '../lib/formatQueryError'
import { resolveApiMediaUrl } from '../lib/resolveApiMediaUrl'

function actorSummaryQueryKey(kinopoiskId: number, userId: string | null) {
  return ['actorSummary', kinopoiskId, userId] as const
}

function actorFilmsQueryKey(kinopoiskId: number, userId: string | null) {
  return ['actorFilms', kinopoiskId, userId] as const
}

export function ActorDetailPage() {
  const { isAuthPending, isAuthReady } = useAuthReadyGate()
  const [searchParams] = useSearchParams()
  const profileUserId = searchParams.get('userId')
  const ownerUserId = profileUserId != null && profileUserId.trim() !== '' ? profileUserId.trim() : null

  const { kinopoiskId: rawId } = useParams<{ kinopoiskId: string }>()
  const parsed = Number(rawId)
  const kinopoiskId = Number.isInteger(parsed) && parsed >= 1 ? parsed : 0

  const summaryQuery = useQuery({
    queryKey: actorSummaryQueryKey(kinopoiskId, ownerUserId),
    queryFn: () => getActorSummary(kinopoiskId, { userId: ownerUserId }),
    enabled: isAuthReady && kinopoiskId >= 1,
    staleTime: 60_000,
  })

  const filmsQuery = useEntitySummaryFilmsPage({
    queryKey: actorFilmsQueryKey(kinopoiskId, ownerUserId),
    fetchPage: ({ cursor, limit }) =>
      getActorFilmsPage(kinopoiskId, { cursor, limit, userId: ownerUserId }),
    entityReady: kinopoiskId >= 1,
    summaryReady: summaryQuery.isSuccess,
  })

  const summary = summaryQuery.data
  const accent = kinopoiskId >= 1 ? directorChipStyles(kinopoiskId) : null
  const actorPhotoSrc =
    summary?.poster_url != null && summary.poster_url.trim() !== ''
      ? (resolveApiMediaUrl(summary.poster_url) ?? summary.poster_url)
      : null

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (kinopoiskId < 1) {
    return (
      <PageErrorState message="Некорректная ссылка на актёра" className="bg-(--tgui--bg_color)" />
    )
  }

  const summaryErr = formatQueryError(summaryQuery.error, 'Не удалось загрузить актёра')

  return (
    <CatalogPageShell headerTitle="Актёр" mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
      {summaryQuery.isPending ? <DetailPageSkeleton /> : null}

      {summaryErr != null ? (
        <ListErrorState
          message={summaryErr}
          onRetry={() => {
            void summaryQuery.refetch()
          }}
        />
      ) : null}

      {summary != null && accent != null ? (
        <>
          <CatalogEntitySummaryCard
            title={summary.name}
            filmsCount={summary.films_count}
            posterUrl={actorPhotoSrc}
            className={`rounded-2xl border px-4 py-4 ${accent.borderClass} ${accent.backgroundClass}`}
          />

          <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
            <h2 className="px-3 pt-3 text-sm font-semibold text-(--tgui--text_color)">
              Ваши оценённые фильмы
            </h2>
            {filmsQuery.films.length === 0 && !filmsQuery.isPending ? (
              <p className="px-3 py-4 text-sm text-(--tgui--hint_color)">
                Пока нет оценённых фильмов с этим актёром
              </p>
            ) : (
              <ul className="divide-y divide-(--tgui--divider_color)">
                {filmsQuery.films.map((film) => {
                  const href =
                    film.my_card_id != null
                      ? `/cards/${film.my_card_id}`
                      : `/films/${film.film_id}`
                  const poster =
                    film.poster_url != null && film.poster_url.trim() !== ''
                      ? (resolveApiMediaUrl(film.poster_url) ?? film.poster_url)
                      : null
                  return (
                    <li key={film.film_id}>
                      <Link
                        to={href}
                        className="flex gap-3 px-3 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)]"
                      >
                        <div className="h-[4.5rem] w-12 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                          {poster != null ? (
                            <img
                              src={poster}
                              alt=""
                              className="h-full w-full object-cover"
                              loading="lazy"
                              decoding="async"
                            />
                          ) : null}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-2 text-sm font-medium text-(--tgui--text_color)">
                            {film.title}
                          </p>
                          {film.role != null && film.role.trim() !== '' ? (
                            <p className="mt-0.5 text-xs text-(--tgui--hint_color)">{film.role}</p>
                          ) : null}
                          <FilmGenreChips genres={film.genres} maxVisible={2} className="mt-1.5" />
                          {film.rating != null ? (
                            <p className="mt-1 text-xs tabular-nums text-(--tgui--hint_color)">
                              Ваша оценка{' '}
                              <span className="font-semibold text-(--tgui--text_color)">
                                {formatRating(film.rating)}
                              </span>
                            </p>
                          ) : null}
                        </div>
                      </Link>
                    </li>
                  )
                })}
              </ul>
            )}
            {filmsQuery.hasNextPage ? (
              <div className="px-3 py-3">
                <button
                  type="button"
                  className="w-full rounded-xl bg-(--tgui--secondary_bg_color) px-4 py-2.5 text-sm font-medium text-(--tgui--text_color)"
                  disabled={filmsQuery.isFetchingNextPage}
                  onClick={() => {
                    void filmsQuery.fetchNextPage()
                  }}
                >
                  {filmsQuery.isFetchingNextPage ? 'Подгружаем…' : 'Подгрузить ещё'}
                </button>
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </CatalogPageShell>
  )
}
