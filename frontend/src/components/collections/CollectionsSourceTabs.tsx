import { SegmentedControl } from '../ui/SegmentedControl'

import {
  COLLECTIONS_CATALOG_SOURCES,
  collectionsCatalogSourceLabel,
  type CollectionsCatalogSource,
} from '../../lib/collectionsCatalogSource'

type CollectionsSourceTabsProps = {
  value: CollectionsCatalogSource
  onChange: (source: CollectionsCatalogSource) => void
  className?: string
}

export function CollectionsSourceTabs({ value, onChange, className }: CollectionsSourceTabsProps) {
  return (
    <SegmentedControl
      value={value}
      onChange={onChange}
      ariaLabel="Источник коллекций"
      className={className}
      segments={COLLECTIONS_CATALOG_SOURCES.map((source) => ({
        value: source,
        label: collectionsCatalogSourceLabel(source),
      }))}
    />
  )
}
