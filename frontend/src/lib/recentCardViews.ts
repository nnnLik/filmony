const MAX_ITEMS = 5
const PREFIX = 'filmony.recent_cards.'

export type RecentCardViewSnapshot = {
  id: number
  film_title: string
  film_poster_url: string | null
  at: number
}

function storageKey(viewerId: string): string {
  return `${PREFIX}${viewerId}`
}

export function readRecentCardViews(viewerId: string): RecentCardViewSnapshot[] {
  if (viewerId === '') return []
  try {
    const raw = localStorage.getItem(storageKey(viewerId))
    if (raw == null || raw === '') return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    const out: RecentCardViewSnapshot[] = []
    for (const item of parsed) {
      if (
        item != null &&
        typeof item === 'object' &&
        typeof (item as RecentCardViewSnapshot).id === 'number' &&
        typeof (item as RecentCardViewSnapshot).film_title === 'string'
      ) {
        const row = item as RecentCardViewSnapshot
        out.push({
          id: row.id,
          film_title: row.film_title,
          film_poster_url: typeof row.film_poster_url === 'string' || row.film_poster_url === null ? row.film_poster_url : null,
          at: typeof row.at === 'number' ? row.at : 0,
        })
      }
    }
    return out
  } catch {
    return []
  }
}

export function recordRecentCardView(viewerId: string, snapshot: Omit<RecentCardViewSnapshot, 'at'>): void {
  if (viewerId === '') return
  const at = Date.now()
  const prev = readRecentCardViews(viewerId).filter((x) => x.id !== snapshot.id)
  const next: RecentCardViewSnapshot[] = [
    { ...snapshot, at },
    ...prev,
  ].slice(0, MAX_ITEMS)
  try {
    localStorage.setItem(storageKey(viewerId), JSON.stringify(next))
    window.dispatchEvent(new CustomEvent('filmony-recent-cards-changed'))
  } catch {
    /* ignore quota / private mode */
  }
}
