import { Section } from '@telegram-apps/telegram-ui'

import { formatQueryError } from '../../lib/formatQueryError'
import { useProfilePinnedCollectionsQuery } from '../../hooks/useProfilePinnedCollectionsQuery'
import { InlineLoadingState } from '../ui/InlineLoadingState'
import { ListErrorState } from '../ui/ListErrorState'
import { TabEmptyState } from '../ui/TabEmptyState'

import { ProfilePinnedCollectionRow } from './ProfilePinnedCollectionRow'

type ProfileCollectionsPanelProps = {
  userId: string
  isOwnProfile?: boolean
  className?: string
}

export function ProfileCollectionsPanel({
  userId,
  isOwnProfile = false,
  className,
}: ProfileCollectionsPanelProps) {
  const query = useProfilePinnedCollectionsQuery(userId)
  const items = query.data?.items ?? []

  if (query.isPending) {
    return (
      <div className={className}>
        <InlineLoadingState message="Загрузка коллекций…" />
      </div>
    )
  }

  const errorMessage = formatQueryError(query.error, 'Не удалось загрузить коллекции')
  if (errorMessage != null) {
    return (
      <div className={className}>
        <ListErrorState
          message={errorMessage}
          onRetry={() => {
            void query.refetch()
          }}
        />
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className={className}>
        <TabEmptyState
          fallback={
            isOwnProfile
              ? 'Закрепите коллекции на странице каталога — они появятся здесь.'
              : 'Пользователь пока не закрепил коллекции.'
          }
          userId={isOwnProfile ? userId : null}
          action={
            isOwnProfile
              ? {
                  label: 'Открыть каталог коллекций',
                  href: '/collections',
                }
              : undefined
          }
        />
      </div>
    )
  }

  return (
    <div className={className}>
      <Section header="Коллекции">
        <ul className="divide-y divide-(--tgui--divider_color)">
          {items.map((collection) => (
            <ProfilePinnedCollectionRow key={collection.slug} collection={collection} />
          ))}
        </ul>
      </Section>
    </div>
  )
}
