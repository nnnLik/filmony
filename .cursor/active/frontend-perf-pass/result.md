# Result: frontend-perf-pass

## Status: complete

## Implemented

### 1. Feed batch badges
- `feedVisibleAuthorIds.ts` + `FeedAuthorBadgesProvider` — page-level streak/taste-quiz batch
- `FeedCard` / `FeedPostCard` use `useFeedCardAuthorBadges` + `registerCommentAuthors`
- Hooks accept optional `staleTime` / `gcTime` (5m / 30m on feed)

### 2. Profile lazy stats chunk
- `ProfileStatsPanel` lazy-loaded on ProfilePage + PublicProfilePage with Suspense
- Separate chunk `ProfileStatsPanel-*.js` (~46 KB raw / ~12 KB gzip)
- Shared profile filters chunk reduced: `useRatedCardsQueryFromUrl` ~73 KB → ~26 KB

### 3. Profile defer eager fetches
- RQ hooks with `enabled` by tab/segment
- Gamification only on movies/rated with cards
- Favorites strip gated; tag stats when filters open or active tag filter
- Monthly recap via RQ (shared cache potential)

### 4. Tailwind trim
- `@source` directives in `index.css`
- Card-detail panel/poster CSS → lazy `movieCardDetailAnimations.css`
- Removed orphan `CreateCardPage.css`
- Removed unused `@telegram-apps/sdk-react` dependency

### 5. Deeplink fix
- `resolveStartParamToPath` + early `history.replaceState` in `main.tsx`
- `AppRoutesGate` render gate during auth + pending deeplink
- Slim idempotent `TelegramMiniAppStartParamRedirect`

### 6. RQ migration Profile
- `profileQueryKeys.ts` + 7 shared hooks
- ProfilePage + PublicProfilePage migrated from useEffect fetches
- ProfileStatsPanel: `useUserMovieCardStatsQuery`, rankings limit 5, unified category keys

## Changed files (main)
- `frontend/src/lib/feedVisibleAuthorIds.ts`, `FeedAuthorBadgesProvider.tsx`, hooks
- `frontend/src/lib/profileQueryKeys.ts`, `frontend/src/hooks/use*Profile*.ts`
- `frontend/src/pages/ProfilePage.tsx`, `PublicProfilePage.tsx`, `FeedPage.tsx`
- `frontend/src/components/feed/FeedCard.tsx`, `FeedPostCard.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`, `ProfileRatedCardsFilters.tsx`
- `frontend/src/lib/miniAppCardDeepLink.ts`, `main.tsx`, `App.tsx`
- `frontend/src/index.css`, `movieCardDetailAnimations.css`
- Tests: `feedVisibleAuthorIds.test.ts`, `miniAppCardDeepLink.test.ts`

## Verification

```bash
cd frontend && npm run lint && npm run build && npm run test
```

- Lint: pass
- Build: pass
- Tests: 90/90 pass

### Bundle (after vs baseline)
| Asset | Before | After |
|-------|--------|-------|
| `useRatedCardsQueryFromUrl` chunk | ~73 KB / ~19 KB gzip | ~26 KB / ~8 KB gzip |
| `ProfileStatsPanel` chunk | (bundled) | ~47 KB / ~12 KB gzip (lazy) |
| `index-*.css` raw | ~140 KB | ~142 KB |
| `index-*.css` gzip | ~19 KB | ~19 KB |

CSS gzip unchanged (card-detail moved to lazy route CSS); main win is profile JS split.

## Known limitations
- PublicProfile keeps eager watchlist fetch (product decision)
- Tailwind `@source` alone did not materially shrink CSS; further gains need dynamic class audit
- Deeplink gate requires manual TMA smoke for all start_param formats

## Next steps (optional)
- Prefetch BottomNav tab chunks on touch
- Narrow Suspense boundary in AppShell
- Backend lightweight favorites-strip endpoint
