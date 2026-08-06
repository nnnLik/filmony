import type { CollectionSummary } from '../../api/collectionsTypes'
import { useAuthStatus } from '../../auth/useAuthStatus'

import { CollectionProgressBar } from './CollectionProgressBar'
import { PinCollectionButton } from './PinCollectionButton'

type CollectionDetailHeaderProps = {
  collection: CollectionSummary
  className?: string
}

export function CollectionDetailHeader({ collection, className }: CollectionDetailHeaderProps) {
  const auth = useAuthStatus()
  const showPinButton = auth.kind === 'ready'

  return (
    <div
      className={`rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-4 ${className ?? ''}`}
    >
      <h1 className="text-lg font-semibold text-(--tgui--text_color)">{collection.title}</h1>
      {collection.description?.trim() ? (
        <p className="filmony-text-panel mt-2 text-sm leading-relaxed text-(--tgui--hint_color)">
          {collection.description}
        </p>
      ) : null}
      <CollectionProgressBar progress={collection.viewer_progress} className="mt-4" />
      {showPinButton ? (
        <PinCollectionButton
          slug={collection.slug}
          isPinned={collection.is_pinned === true}
          className="mt-4"
        />
      ) : null}
    </div>
  )
}
