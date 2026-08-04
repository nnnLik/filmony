# Frontend performance pass

Six coordinated optimizations to reduce HTTP noise, defer non-critical work, split heavy chunks, and fix Telegram deeplink flash.

## Feed batch badges

Global feed aggregates author IDs at page level via `FeedAuthorBadgesProvider`. Streak and taste-quiz knowledge batch APIs are called once per visible feed page (plus merged comment authors when panels expand), instead of per card.

## Profile lazy stats

`ProfileStatsPanel` (charts, heatmap, passport) loads only when the stats tab is opened. Applies to `/profile` and `/u/:userId`.

## Profile data fetching

Profile and public profile pages use React Query with tab/segment `enabled` flags:

- Rated cards, watchlist, posts — only when the corresponding tab/segment is active
- Gamification — movies/rated tab with cards
- Tag filter stats — when filter panel open or tag filter active
- Monthly recap — separate query, not blocking profile shell

Tab switches reuse cache within `staleTime`.

## Tailwind / CSS

- Explicit `@source` scan paths in `index.css`
- Movie card detail animations in lazy `movieCardDetailAnimations.css`
- Shared fade-in keyframes remain global for sheets/toasts

## Telegram deeplinks

`resolveStartParamToPath` consolidates start_param parsing. Early URL rewrite in `main.tsx` avoids matching `/` (Feed) before redirect. `AppRoutesGate` shows fallback while auth bootstraps with a pending deeplink.

## Verification

```bash
cd frontend && npm run lint && npm run build && npm run test
```

## Related files

- [`frontend/src/lib/profileQueryKeys.ts`](../../frontend/src/lib/profileQueryKeys.ts)
- [`frontend/src/context/FeedAuthorBadgesProvider.tsx`](../../frontend/src/context/FeedAuthorBadgesProvider.tsx)
- [`frontend/src/lib/miniAppCardDeepLink.ts`](../../frontend/src/lib/miniAppCardDeepLink.ts)
