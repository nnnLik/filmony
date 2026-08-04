# Frontend Refactor + UX Polish Pack

## Summary

Large-scale frontend refactor consolidating duplicated UI patterns and delivering UX improvements across feed, catalog, profile, and community pages.

## UI primitives

| Component | Purpose |
|-----------|---------|
| `PageLoadingState` | Full-page auth/loading gate |
| `PageErrorState` | Full-page error + retry/back |
| `TabEmptyState` | PlayfulHint + optional CTA |
| `DetailPageSkeleton` | Detail page loading placeholder |
| `StickyBackHeader` | Unified catalog back navigation |

## Comment thread architecture

Shared hooks under `frontend/src/hooks/useComment*.ts` and components under `frontend/src/components/comments/`. Feed cards use in-panel comment jump (Telegram-like) via `CommentParentQuote` + `useCommentScrollHighlight`.

## Feed improvements

- **«Для вас» tab** — recommendation feed (`GET /api/cards/feed`) with explainability chips
- **OfflineFeedBanner** — prominent stale cache indicator with refresh
- **useGlobalFeed** — extracted feed data layer from `FeedPage`

## Catalog & games

- Shared `CatalogPageShell`, `CatalogFilmsSection` for index/detail pages
- `TitleCommunityDetailLayout` for film + catalog community detail
- Route alias: `/games/:catalogItemId` → catalog detail page
- Search links catalog/game hits to community pages

## Profile

Shared tab panels: `ProfileRatedPanel`, `ProfileWatchlistPanel`, `ProfilePostsPanel`, `ProfileStatsTab`.

## Search

- Unified debounce: `CATALOG_SEARCH_DEBOUNCE_MS = 400` (`lib/catalogSearchTiming.ts`)
- `SearchResultsSkeleton` during debounce/fetch

## Social polish

- `FollowingRatingsPanel` loading skeleton + subscriptions empty CTA
- `CommunityRatingsList` «Сначала друзья» client filter
- Watchlist overlap micro-hint on profile; catalog watchlist parity with films

## Verification

```bash
cd frontend && npm run lint && npm run build
```
