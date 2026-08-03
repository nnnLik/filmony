# Offline feed cache

## Scope
- Persist first page of global feed (`/`) in IndexedDB per user/kind/hideMine.
- Show cached feed on offline/network error with stale banner.
- Clear cache on auth logout.

## Acceptance criteria
- `globalFeedCacheStorage.ts` with 24h TTL, first-page-only snapshot.
- `FeedPage` hydrates from cache, writes on successful fetch, stale banner.
- Vitest for storage; `npm run lint && npm run build` pass.
