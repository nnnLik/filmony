import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'

import { getGenreFilmsPage, getGenreSummary } from '../api/genresApi'
import { CatalogEntitySummaryCard } from '../components/catalog/CatalogEntitySummaryCard'
import { CatalogFilmsSection } from '../components/catalog/CatalogFilmsSection'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { DetailPageSkeleton } from '../components/ui/DetailPageSkeleton'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useEntitySummaryFilmsPage } from '../hooks/useEntitySummaryFilmsPage'
import { formatQueryError } from '../lib/formatQueryError'

function genreSummaryQueryKey(slug: string) {
  return ['genreSummary', slug] as const
}

function genreFilmsQueryKey(slug: string) {
  return ['genreFilms', slug] as const
}

export function GenreDetailPage() {
  const { isAuthPending, isAuthReady } = useAuthReadyGate()
  const { slug: rawSlug } = useParams<{ slug: string }>()
  const slug = rawSlug?.trim() ?? ''

  const summaryQuery = useQuery({
    queryKey: genreSummaryQueryKey(slug),
    queryFn: () => getGenreSummary(slug),
    enabled: isAuthReady && slug !== '',
    staleTime: 60_000,
  })

  const filmsQuery = useEntitySummaryFilmsPage({
    queryKey: genreFilmsQueryKey(slug),
    fetchPage: ({ cursor, limit }) => getGenreFilmsPage(slug, { cursor, limit }),
    entityReady: slug !== '',
    summaryReady: summaryQuery.isSuccess,
  })

  const summary = summaryQuery.data

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (slug === '') {
    return <PageErrorState message="Некорректная ссылка на жанр" className="bg-(--tgui--bg_color)" />
  }

  const summaryErr = formatQueryError(summaryQuery.error, 'Не удалось загрузить жанр')

  return (
    <CatalogPageShell headerTitle="Жанр" mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
      {summaryQuery.isPending ? <DetailPageSkeleton /> : null}

      {summaryErr != null ? (
        <ListErrorState
          message={summaryErr}
          onRetry={() => {
            void summaryQuery.refetch()
          }}
        />
      ) : null}

      {summary != null ? (
        <>
          <CatalogEntitySummaryCard
            title={summary.genre}
            filmsCount={summary.films_count}
            avgCommunityRating={summary.avg_community_rating}
            className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-4"
            footer={
              summary.top_genres.length > 0 ? (
                <FilmGenreChips genres={summary.top_genres} maxVisible={4} className="mt-3" />
              ) : null
            }
          />

          <CatalogFilmsSection
            films={filmsQuery.films}
            isPending={filmsQuery.isPending}
            emptyMessage="Пока нет оценённых фильмов этого жанра"
            hasNextPage={filmsQuery.hasNextPage}
            isFetchingNextPage={filmsQuery.isFetchingNextPage}
            onLoadMore={() => {
              void filmsQuery.fetchNextPage()
            }}
          />
        </>
      ) : null}
    </CatalogPageShell>
  )
}
