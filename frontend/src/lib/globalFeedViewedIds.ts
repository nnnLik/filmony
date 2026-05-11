/** Локально: какие карточки/посты открывали с детальной (для подсветки в глобальной ленте). */

const STORAGE_KEY = 'filmony.globalFeed.viewedIds.v1'
const MAX_IDS_PER_KIND = 800

type Store = { c: number[]; p: number[] }

function readStore(): Store {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw == null || raw === '') return { c: [], p: [] }
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null) return { c: [], p: [] }
    const c = (parsed as { c?: unknown }).c
    const p = (parsed as { p?: unknown }).p
    return {
      c: Array.isArray(c) ? c.filter((x): x is number => typeof x === 'number' && Number.isInteger(x)) : [],
      p: Array.isArray(p) ? p.filter((x): x is number => typeof x === 'number' && Number.isInteger(x)) : [],
    }
  } catch {
    return { c: [], p: [] }
  }
}

function writeStore(s: Store): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  } catch {
    /* ignore */
  }
}

function pushId(list: number[], id: number): number[] {
  const next = list.filter((x) => x !== id)
  next.unshift(id)
  return next.slice(0, MAX_IDS_PER_KIND)
}

export function markGlobalFeedCardDetailOpened(cardId: number): void {
  const s = readStore()
  s.c = pushId(s.c, cardId)
  writeStore(s)
}

export function markGlobalFeedPostDetailOpened(postId: number): void {
  const s = readStore()
  s.p = pushId(s.p, postId)
  writeStore(s)
}

export function isGlobalFeedCardDetailOpened(cardId: number): boolean {
  return readStore().c.includes(cardId)
}

export function isGlobalFeedPostDetailOpened(postId: number): boolean {
  return readStore().p.includes(postId)
}
