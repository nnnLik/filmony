import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'

import { getFranchiseFilmsPage, getFranchiseSummary } from '../api/franchisesApi'
import { CatalogEntitySummaryCard } from '../components/catalog/CatalogEntitySummaryCard'
import { CatalogFilmsSection } from '../components/catalog/CatalogFilmsSection'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { DetailPageSkeleton } from '../components/ui/DetailPageSkeleton'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useEntitySummaryFilmsPage } from '../hooks/useEntitySummaryFilmsPage'
import { formatQueryError } from '../lib/formatQueryError'
import { franchiseChipStyles } from '../lib/franchiseColor'

function franchiseSummaryQueryKey(franchiseKey: string) {
  return ['franchiseSummary', franchiseKey] as const
}

function franchiseFilmsQueryKey(franchiseKey: string) {
  return ['franchiseFilms', franchiseKey] as const
}

export function FranchiseDetailPage() {
  const { isAuthPending, isAuthReady } = useAuthReadyGate()
  const { franchiseKey: rawKey } = useParams<{ franchiseKey: string }>()
  const franchiseKey = rawKey?.trim() ?? ''

  const summaryQuery = useQuery({
    queryKey: franchiseSummaryQueryKey(franchiseKey),
    queryFn: () => getFranchiseSummary(franchiseKey),
    enabled: isAuthReady && franchiseKey !== '',
    staleTime: 60_000,
  })

  const filmsQuery = useEntitySummaryFilmsPage({
    queryKey: franchiseFilmsQueryKey(franchiseKey),
    fetchPage: ({ cursor, limit }) => getFranchiseFilmsPage(franchiseKey, { cursor, limit }),
    entityReady: franchiseKey !== '',
    summaryReady: summaryQuery.isSuccess,
  })

  const summary = summaryQuery.data
  const accent = franchiseKey !== '' ? franchiseChipStyles(franchiseKey) : null

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (franchiseKey === '') {
    return <PageErrorState message="Некорректная ссылка на франшизу" className="bg-(--tgui--bg_color)" />
  }

  const summaryErr = formatQueryError(summaryQuery.error, 'Не удалось загрузить франшизу')

  return (
    <CatalogPageShell headerTitle="Франшиза" mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
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
            title={summary.label}
            filmsCount={summary.films_count}
            avgCommunityRating={summary.avg_community_rating}
            className={`rounded-2xl border px-4 py-4 ${accent.borderClass} ${accent.backgroundClass}`}
          />

          <CatalogFilmsSection
            films={filmsQuery.films}
            isPending={filmsQuery.isPending}
            emptyMessage="Пока нет оценённых фильмов этой франшизы"
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
