# Offline feed cache

## Summary
First page of the global feed is cached in IndexedDB (24h TTL) so Telegram WebView users see the last loaded feed when the network fails.

## Behavior
- Key: user id + feed kind (`all`/`posts`/`cards`) + hide-mine toggle.
- On mount: read cache → `setQueryData` before fetch completes.
- On success: write first page to IndexedDB.
- On error with cached items: show feed + banner «Данные от …» + optional retry.
- Logout clears all feed cache entries.

## Files
- `frontend/src/lib/globalFeedCacheStorage.ts`
- `frontend/src/pages/FeedPage.tsx`

## Verification
```bash
cd frontend && npm run lint && npm run test && npm run build
```
