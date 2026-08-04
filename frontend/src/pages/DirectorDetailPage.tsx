import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'

import { getDirectorFilmsPage, getDirectorSummary } from '../api/directorsApi'
import { CatalogEntitySummaryCard } from '../components/catalog/CatalogEntitySummaryCard'
import { CatalogFilmsSection } from '../components/catalog/CatalogFilmsSection'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { DetailPageSkeleton } from '../components/ui/DetailPageSkeleton'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useEntitySummaryFilmsPage } from '../hooks/useEntitySummaryFilmsPage'
import { directorChipStyles } from '../lib/directorColor'
import { formatQueryError } from '../lib/formatQueryError'
import { resolveApiMediaUrl } from '../lib/resolveApiMediaUrl'

function directorSummaryQueryKey(kinopoiskId: number) {
  return ['directorSummary', kinopoiskId] as const
}

function directorFilmsQueryKey(kinopoiskId: number) {
  return ['directorFilms', kinopoiskId] as const
}

export function DirectorDetailPage() {
  const { isAuthPending, isAuthReady } = useAuthReadyGate()
  const { kinopoiskId: rawId } = useParams<{ kinopoiskId: string }>()
  const parsed = Number(rawId)
  const kinopoiskId = Number.isInteger(parsed) && parsed >= 1 ? parsed : 0

  const summaryQuery = useQuery({
    queryKey: directorSummaryQueryKey(kinopoiskId),
    queryFn: () => getDirectorSummary(kinopoiskId),
    enabled: isAuthReady && kinopoiskId >= 1,
    staleTime: 60_000,
  })

  const filmsQuery = useEntitySummaryFilmsPage({
    queryKey: directorFilmsQueryKey(kinopoiskId),
    fetchPage: ({ cursor, limit }) => getDirectorFilmsPage(kinopoiskId, { cursor, limit }),
    entityReady: kinopoiskId >= 1,
    summaryReady: summaryQuery.isSuccess,
  })

  const summary = summaryQuery.data
  const accent = kinopoiskId >= 1 ? directorChipStyles(kinopoiskId) : null
  const directorPhotoSrc =
    summary?.poster_url != null && summary.poster_url.trim() !== ''
      ? (resolveApiMediaUrl(summary.poster_url) ?? summary.poster_url)
      : null

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (kinopoiskId < 1) {
    return (
      <PageErrorState message="Некорректная ссылка на режиссёра" className="bg-(--tgui--bg_color)" />
    )
  }

  const summaryErr = formatQueryError(summaryQuery.error, 'Не удалось загрузить режиссёра')

  return (
    <CatalogPageShell headerTitle="Режиссёр" mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
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
            avgCommunityRating={summary.avg_community_rating}
            posterUrl={directorPhotoSrc}
            className={`rounded-2xl border px-4 py-4 ${accent.borderClass} ${accent.backgroundClass}`}
          />

          <CatalogFilmsSection
            films={filmsQuery.films}
            isPending={filmsQuery.isPending}
            emptyMessage="Пока нет оценённых фильмов этого режиссёра"
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
