import { Title } from '@telegram-apps/telegram-ui'
import { useMemo } from 'react'

import { getGenresCatalogPage } from '../api/genresApi'
import { CatalogIndexList } from '../components/catalog/CatalogIndexList'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useCursorInfiniteList } from '../hooks/useCursorInfiniteList'
import { formatQueryError } from '../lib/formatQueryError'

function genresCatalogQueryKey() {
  return ['genresCatalog'] as const
}

export function GenresIndexPage() {
  const { isAuthPending } = useAuthReadyGate()

  const catalogQuery = useCursorInfiniteList({
    queryKey: genresCatalogQueryKey(),
    queryFn: ({ cursor, limit }) => getGenresCatalogPage({ cursor, limit }),
    limit: 50,
  })

  const listItems = useMemo(
    () =>
      catalogQuery.items.map((row) => ({
        key: row.slug,
        label: row.genre,
        href: `/genres/${encodeURIComponent(row.slug)}`,
        filmsCount: row.films_count,
      })),
    [catalogQuery.items],
  )

  const listErr = formatQueryError(catalogQuery.error, 'Не удалось загрузить жанры')

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  return (
    <CatalogPageShell headerTitle="Жанры">
      <Title level="2" weight="2">
        Жанры в Filmony
      </Title>
      <p className="mt-1 text-sm text-(--tgui--hint_color)">
        Фильмы с оценками сообщества, сгруппированные по жанру.
      </p>

      <CatalogIndexList
        items={listItems}
        isPending={catalogQuery.isPending}
        errorMessage={listErr}
        onRetry={() => {
          void catalogQuery.refetch()
        }}
        emptyMessage="Пока нет жанров в каталоге"
        hasNextPage={catalogQuery.hasNextPage}
        isFetchingNextPage={catalogQuery.isFetchingNextPage}
        onLoadMore={() => {
          void catalogQuery.fetchNextPage()
        }}
      />
    </CatalogPageShell>
  )
}
