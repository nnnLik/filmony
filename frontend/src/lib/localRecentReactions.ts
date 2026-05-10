import type { ReactionCatalogItem, ReactionGroupedCatalog } from '../api/profileTypes'

const STORAGE_KEY = 'filmony.recentReactionTypeIds.v1'
const MAX_ITEMS = 16

export function readRecentReactionTypeIds(): number[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw == null || raw === '') return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    const ids: number[] = []
    for (const x of parsed) {
      if (typeof x === 'number' && Number.isInteger(x) && x > 0) ids.push(x)
    }
    return ids
  } catch {
    return []
  }
}

/** Последний выбор — в начало списка, без дубликатов. */
export function recordRecentReactionTypeId(reactionTypeId: number): void {
  if (!Number.isInteger(reactionTypeId) || reactionTypeId <= 0) return
  const prev = readRecentReactionTypeIds().filter((id) => id !== reactionTypeId)
  const next = [reactionTypeId, ...prev].slice(0, MAX_ITEMS)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    /* quota / private mode */
  }
}

function catalogItemById(catalog: ReactionGroupedCatalog): Map<number, ReactionCatalogItem> {
  const m = new Map<number, ReactionCatalogItem>()
  for (const tab of catalog.tabs) {
    for (const it of tab.items) {
      m.set(it.id, it)
    }
  }
  return m
}

/** Строит список для блока «Недавние» по сохранённым id и загруженному каталогу. */
export function resolveRecentCatalogItems(
  catalog: ReactionGroupedCatalog | null,
  orderedIds: number[],
): ReactionCatalogItem[] {
  if (catalog == null || orderedIds.length === 0) return []
  const byId = catalogItemById(catalog)
  const out: ReactionCatalogItem[] = []
  for (const id of orderedIds) {
    const item = byId.get(id)
    if (item != null) out.push(item)
  }
  return out
}
