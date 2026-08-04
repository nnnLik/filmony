import { Title } from '@telegram-apps/telegram-ui'
import { useMemo } from 'react'

import { getDirectorsCatalogPage } from '../api/directorsApi'
import { CatalogIndexList } from '../components/catalog/CatalogIndexList'
import { CatalogPageShell } from '../components/layout/CatalogPageShell'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useCursorInfiniteList } from '../hooks/useCursorInfiniteList'
import { directorChipStyles } from '../lib/directorColor'
import { formatQueryError } from '../lib/formatQueryError'

function directorsCatalogQueryKey() {
  return ['directorsCatalog'] as const
}

export function DirectorsIndexPage() {
  const { isAuthPending } = useAuthReadyGate()

  const catalogQuery = useCursorInfiniteList({
    queryKey: directorsCatalogQueryKey(),
    queryFn: ({ cursor, limit }) => getDirectorsCatalogPage({ cursor, limit }),
    limit: 50,
  })

  const listItems = useMemo(
    () =>
      catalogQuery.items.map((row) => ({
        key: String(row.kinopoisk_id),
        label: row.name,
        href: `/directors/${row.kinopoisk_id}`,
        filmsCount: row.films_count,
        linkClassName: directorChipStyles(row.kinopoisk_id).backgroundClass,
      })),
    [catalogQuery.items],
  )

  const listErr = formatQueryError(catalogQuery.error, 'Не удалось загрузить режиссёров')

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  return (
    <CatalogPageShell headerTitle="Режиссёры">
      <Title level="2" weight="2">
        Режиссёры в Filmony
      </Title>
      <p className="mt-1 text-sm text-(--tgui--hint_color)">
        Фильмы с оценками сообщества, сгруппированные по режиссёру.
      </p>

      <CatalogIndexList
        items={listItems}
        isPending={catalogQuery.isPending}
        errorMessage={listErr}
        onRetry={() => {
          void catalogQuery.refetch()
        }}
        emptyMessage="Пока нет режиссёров в каталоге"
        hasNextPage={catalogQuery.hasNextPage}
        isFetchingNextPage={catalogQuery.isFetchingNextPage}
        onLoadMore={() => {
          void catalogQuery.fetchNextPage()
        }}
      />
    </CatalogPageShell>
  )
}
