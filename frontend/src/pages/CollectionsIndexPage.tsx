import { useState } from 'react'

import { CollectionListItem } from '../components/collections/CollectionListItem'
import { CollectionsSourceTabs } from '../components/collections/CollectionsSourceTabs'
import { PageHeader } from '../components/layout/PageHeader'
import { InlineLoadingState } from '../components/ui/InlineLoadingState'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { TabEmptyState } from '../components/ui/TabEmptyState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useCollectionsList } from '../hooks/useCollectionsList'
import {
  collectionKindForCatalogSource,
  collectionsCatalogEmptyMessage,
  collectionsCatalogSubtitle,
  type CollectionsCatalogSource,
} from '../lib/collectionsCatalogSource'
import { formatQueryError } from '../lib/formatQueryError'

export function CollectionsIndexPage() {
  const { isAuthPending } = useAuthReadyGate()
  const [source, setSource] = useState<CollectionsCatalogSource>('letterboxd')
  const kind = collectionKindForCatalogSource(source)
  const collectionsQuery = useCollectionsList(kind)

  const listErr = formatQueryError(collectionsQuery.error, 'Не удалось загрузить коллекции')
  const items = collectionsQuery.data?.items ?? []

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  return (
    <div className="min-h-full bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <PageHeader
        title="Коллекции"
        tabs={<CollectionsSourceTabs value={source} onChange={setSource} />}
        subtitle={
          <p className="mt-2 text-[12px] leading-snug text-(--tgui--hint_color)">
            {collectionsCatalogSubtitle(source)}
          </p>
        }
      />
      <main className="mx-auto max-w-md space-y-4 px-4 pb-4 pt-4">
        {collectionsQuery.isPending ? (
          <InlineLoadingState message="Загружаем коллекции…" />
        ) : null}

        {listErr != null ? (
          <ListErrorState
            message={listErr}
            onRetry={() => {
              void collectionsQuery.refetch()
            }}
          />
        ) : null}

        {!collectionsQuery.isPending && listErr == null && items.length === 0 ? (
          <TabEmptyState fallback={collectionsCatalogEmptyMessage(source)} className="py-8" />
        ) : null}

        {items.length > 0 ? (
          <ul className="space-y-3">
            {items.map((collection) => (
              <CollectionListItem key={collection.slug} collection={collection} />
            ))}
          </ul>
        ) : null}
      </main>
    </div>
  )
}
