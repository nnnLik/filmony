import { Title } from '@telegram-apps/telegram-ui'

import { CollectionListItem } from '../components/collections/CollectionListItem'
import { PageHeader } from '../components/layout/PageHeader'
import { InlineLoadingState } from '../components/ui/InlineLoadingState'
import { ListErrorState } from '../components/ui/ListErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { TabEmptyState } from '../components/ui/TabEmptyState'
import { useAuthReadyGate } from '../hooks/useAuthReadyGate'
import { useCollectionsList } from '../hooks/useCollectionsList'
import { formatQueryError } from '../lib/formatQueryError'

export function CollectionsIndexPage() {
  const { isAuthPending } = useAuthReadyGate()
  const collectionsQuery = useCollectionsList()

  const listErr = formatQueryError(collectionsQuery.error, 'Не удалось загрузить коллекции')
  const items = collectionsQuery.data?.items ?? []

  if (isAuthPending) {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  return (
    <div className="min-h-full bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <PageHeader title="Коллекции" />
      <main className="mx-auto max-w-md space-y-4 px-4 pb-4 pt-4">
        <div>
          <Title level="2" weight="2">
            Подборки Filmony
          </Title>
          <p className="mt-1 text-sm text-(--tgui--hint_color)">
            Кураторские списки фильмов — отмечайте прогресс по мере оценок.
          </p>
        </div>

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
          <TabEmptyState fallback="Пока нет активных коллекций." className="py-8" />
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
