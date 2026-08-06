export const collectionsQueryRootKey = ['collections'] as const

export const collectionsListQueryKey = (kind?: string) =>
  [...collectionsQueryRootKey, 'list', kind ?? 'all'] as const

export const collectionDetailQueryKey = (slug: string) =>
  [...collectionsQueryRootKey, 'detail', slug] as const

export const collectionFilmsQueryKey = (slug: string) =>
  [...collectionsQueryRootKey, 'films', slug] as const

export const profilePinnedCollectionsQueryKey = (userId: string) =>
  [...collectionsQueryRootKey, 'profilePinned', userId] as const
