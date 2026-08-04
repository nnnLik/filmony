# Result: frontend-ui-boot-polish

## Status: completed

## Implemented

- Shared layout/UI chrome under `frontend/src/components/layout/` and `frontend/src/components/ui/`
- FeedPage + ProfilePage use PageHeader, SegmentedControl (pill tabs), shared empty/error/loading states
- BottomNav uses lucide Home/User; Profile settings uses lucide Settings in IconButton
- Auth bootstrap parallelized: bearer + cookie (credentials-only) + initData wait overlap
- Boot defer: `scheduleIdleWork`, deferred pepe/disco prewarm, idle-gated mention subscriptions, compose prefetch

## Changed files

- `frontend/src/components/layout/PageHeader.tsx` (new)
- `frontend/src/components/ui/SegmentedControl.tsx` (new)
- `frontend/src/components/ui/EmptyState.tsx` (new)
- `frontend/src/components/ui/ListErrorState.tsx` (new)
- `frontend/src/components/ui/InlineLoadingState.tsx` (new)
- `frontend/src/lib/scheduleIdleWork.ts` (new)
- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/SearchPage.tsx`
- `frontend/src/components/navigation/BottomNav.tsx`
- `frontend/src/auth/authBootstrap.ts` (new)
- `frontend/src/auth/AuthProvider.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/lib/pepeGif.ts`
- `frontend/src/layout/AppShell.tsx`
- `frontend/src/components/MentionProfileLookupBootstrap.tsx`
- `frontend/src/compose/ComposeFeedPostProvider.tsx`

## Tests

- `frontend/src/auth/authBootstrap.test.ts` — bearer ok, stale bearer + cookie ok, telegram fallback
- `frontend/src/lib/scheduleIdleWork.test.ts` — setTimeout fallback

## Verification

```bash
cd frontend && npm run lint && npm run test && npm run build
```

- lint: pass
- test: 50 passed
- build: pass

## Known limitations

- Nested Profile «Оценённые / Позже» tabs not migrated to SegmentedControl (v2)
- Other sticky headers (Search detail pages, etc.) unchanged
- Feed still gated on `auth.ready` (no early public feed)
