# Frontend UI boot polish

Starter pack for visual consistency on Feed/Profile/BottomNav and faster TMA boot.

## UI consistency

- **PageHeader** — sticky gradient title + optional pepe, actions/tabs/subtitle slots
- **SegmentedControl** — pill tabs shared by Feed kind filter and Profile main tabs
- **EmptyState / ListErrorState / InlineLoadingState** — unified list chrome on Feed; Profile auth/loading uses InlineLoadingState
- **BottomNav** — lucide `Home` / `Search` / `User`
- **Profile settings** — lucide `Settings` in TGUI `IconButton`

## Boot performance

- **Auth** — bearer resume, cookie probe (no stale Bearer), and initData polling start in parallel (`authBootstrap.ts`)
- **Pepe/disco** — dancing Pepe preloads on idle; disco rain deferred to desktop idle or first side-Pepe click; AppShell no longer prewarms both GIFs on every mount
- **Mentions** — following subscriptions query deferred via idle callback; compose open prefetches same React Query key

## Verification

```bash
cd frontend && npm run lint && npm run test && npm run build
```

Tests: `authBootstrap.test.ts`, `scheduleIdleWork.test.ts`.
