# Frontend UI boot polish

## Goal

Improve perceived quality and boot performance for the Telegram Mini App starter surfaces (Feed, Profile, BottomNav) without a full redesign.

## Scope

- Shared chrome: PageHeader, SegmentedControl, EmptyState, ListErrorState, InlineLoadingState
- Migrate FeedPage, ProfilePage, BottomNav
- Parallel auth resume probes + credentials-only cookie probe
- Defer pepe/disco prewarm and mention subscriptions bootstrap; prefetch following on compose open

## Out of scope

- Feed virtualization, rating palette, bulk header migration, early public feed before auth.ready, backend changes

## Acceptance criteria

- Feed and Profile headers/tabs visually aligned (pill segments)
- BottomNav + Profile settings use lucide + IconButton
- Auth resume probes run in parallel; cookie path works with invalid stored Bearer
- No GIF dual-preload on every AppShell mount; compose @-picker has following list
- `npm run lint && npm run test && npm run build` green
