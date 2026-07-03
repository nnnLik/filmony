import type { CategoryDistributionItem, MyUserCardCategory } from '../api/profileTypes'

export function mergeShelfDistributionWithMetadata(
  distribution: CategoryDistributionItem[],
  shelves: readonly MyUserCardCategory[],
): CategoryDistributionItem[] {
  if (shelves.length === 0) {
    return distribution
  }

  const byCategoryId = new Map<number, CategoryDistributionItem>()
  const uncategorizedRows: CategoryDistributionItem[] = []

  for (const row of distribution) {
    if (row.category_id == null) {
      uncategorizedRows.push(row)
      continue
    }
    byCategoryId.set(row.category_id, row)
  }

  const mergedShelves: CategoryDistributionItem[] = shelves.map((shelf) => {
    const row = byCategoryId.get(shelf.id)
    return {
      category_id: shelf.id,
      name: shelf.name,
      count: row?.count ?? 0,
    }
  })

  return [...mergedShelves, ...uncategorizedRows]
}
