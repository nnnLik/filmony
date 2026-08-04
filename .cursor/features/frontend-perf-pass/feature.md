# Frontend performance pass

## Scope
Six coordinated frontend optimizations:
1. Feed batch badges (page-level aggregation)
2. Profile lazy stats chunk
3. Profile defer eager fetches
4. Tailwind CSS trim
5. Telegram deeplink without Feed flash
6. Profile + PublicProfile React Query migration

## Acceptance criteria
- Feed: 2 batch badge HTTP calls on initial load (~20 cards), not N×2 per card
- Profile/PublicProfile: stats UI in separate lazy chunk; cold open ≤3 critical HTTP
- Tab switches use RQ cache (no refetch within staleTime)
- Main CSS gzip reduced vs baseline (target −15 KB gzip minimum)
- TMA deeplink `c{id}` / `f{id}`: no FeedPage flash
- `cd frontend && npm run lint && npm run build && npm run test` pass
- Feature docs + action log updated

## Notes
- PublicProfile keeps eager watchlist fetch (product behavior)
- Detail pages (MovieCardDetail, FeedPostDetail) keep local badge hooks
