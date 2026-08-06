import { Link } from 'react-router'

import type { CollectionSummary } from '../../api/collectionsTypes'
import { CollectionProgressBar } from '../collections/CollectionProgressBar'

type ProfilePinnedCollectionRowProps = {
  collection: CollectionSummary
}

export function ProfilePinnedCollectionRow({ collection }: ProfilePinnedCollectionRowProps) {
  const description = collection.description?.trim()

  return (
    <li>
      <Link
        to={`/collections/${encodeURIComponent(collection.slug)}`}
        className="block px-4 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)"
      >
        <p className="text-sm font-medium text-(--tgui--text_color)">{collection.title}</p>
        {description != null && description !== '' ? (
          <p className="filmony-text-panel mt-1 line-clamp-2 text-sm text-(--tgui--hint_color)">
            {description}
          </p>
        ) : null}
        <CollectionProgressBar progress={collection.viewer_progress} className="mt-2" />
      </Link>
    </li>
  )
}
