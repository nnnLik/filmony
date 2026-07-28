# Pet-project micro-fun

Playful copy and a hidden feed scroll easter egg for the small Filmony circle.

## Scope

1. **Empty states** — deterministic daily rotation of playful Russian hints on feed, comments, profile posts/cards, and search.
2. **Create card watch note** — rotating placeholder in the rated-card form note field.
3. **Scroll depth secret** — after three bottom-of-feed visits in one session (all pages loaded), show a toast + Telegram haptic once.

## Copy

All phrases live in [`frontend/src/lib/microFun/microFunCopy.ts`](../../frontend/src/lib/microFun/microFunCopy.ts). Edit pools there; no backend.

Selection is stable per user + pool + UTC day via [`pickMicroFunLine`](../../frontend/src/lib/microFun/pickMicroFunLine.ts).

## UI integration

| Surface | Component / hook |
|---------|------------------|
| Feed empty | `EmptyState` + `playfulKey="feed_empty"` |
| Comments empty | `PlayfulHint` |
| Profile / search empties | `PlayfulHint` or `EmptyState` |
| Watch note placeholder | `useMicroFunLine('watch_note_placeholder')` in `RatedCardScrollForm` |
| Feed scroll secret | `useFeedScrollDepthSecret` + `MicroFunToast` on `FeedPage` |

## Scroll secret rules

- Listener on Feed `main` scroll container (same as scroll restore).
- Counts only when `!hasNextPage && !isFetchingNextPage` and `items.length > 0`.
- Session state in `sessionStorage` key `filmony.feed-scroll-secret.v1:{userId}`.
- Toast auto-dismisses after 3s; respects `prefers-reduced-motion` (no fade animation).

## Out of scope

- Stats/filter empty states stay neutral.
- No Pepe/GIF changes for scroll secret (toast + haptic only).

## Verification

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm test -- --run pickMicroFunLine feedScrollDepthSecret
```
