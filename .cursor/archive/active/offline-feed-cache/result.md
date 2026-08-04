# Result: offline-feed-cache

## Status
done

## Implemented
- IndexedDB cache (`idb-keyval`) for first global feed page per user/tab/hideMine.
- FeedPage offline UX: hydrate from cache, stale banner, retry on error.
- Cache cleared on auth logout.

## Files
- `frontend/src/lib/globalFeedCacheStorage.ts`
- `frontend/src/lib/globalFeedCacheStorage.test.ts`
- `frontend/src/lib/formatOfflineCacheTimestamp.ts`
- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/auth/authBootstrap.ts`

## Verification
- `npm run lint && npm run test && npm run build` — pass (65 tests)
