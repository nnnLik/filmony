import { useParams } from 'react-router'

import { CollectionDetailHeader } from '../components/collections/CollectionDetailHeader'
import { CollectionFilmsList } from '../components/collections/CollectionFilmsList'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { DetailPageSkeleton } from '../components/ui/DetailPageSkeleton'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useCollectionDetail } from '../hooks/useCollectionDetail'
import { useCollectionFilmsInfinite } from '../hooks/useCollectionFilmsInfinite'
import { formatQueryError } from '../lib/formatQueryError'

export function CollectionDetailPage() {
  const { isAuthPending } = useAuthReadyGate()
  const { slug: rawSlug } = useParams<{ slug: string }>()
  const slug = rawSlug?.trim() ?? ''

  const summaryQuery = useCollectionDetail(slug)
  const filmsQuery = useCollectionFilmsInfinite(slug, {
    enabled: summaryQuery.isSuccess,
  })

  const collection = summaryQuery.data

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (slug === '') {
    return (
      <PageErrorState message="Некорректная ссылка на коллекцию" className="bg-(--tgui--bg_color)" />
    )
  }

  const summaryErr = formatQueryError(summaryQuery.error, 'Не удалось загрузить коллекцию')
  const filmsErr = formatQueryError(filmsQuery.error, 'Не удалось загрузить фильмы')

  return (
    <CatalogPageShell headerTitle="Коллекция" mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
      {summaryQuery.isPending ? <DetailPageSkeleton /> : null}

      {summaryErr != null ? (
        <ListErrorState
          message={summaryErr}
          onRetry={() => {
            void summaryQuery.refetch()
          }}
        />
      ) : null}

      {collection != null ? (
        <>
          <CollectionDetailHeader collection={collection} />

          <CollectionFilmsList
            films={filmsQuery.films}
            isPending={filmsQuery.isPending}
            errorMessage={filmsErr}
            onRetry={() => {
              void filmsQuery.refetch()
            }}
            hasNextPage={filmsQuery.hasNextPage ?? false}
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
