# Profile streak explainer + donut legend collapse + remove rated marathon shelf + remove Posts tab

## Metadata
- Feature slug: `profile-streak-stats-legend-ux`
- Author: Agent
- Created at: 2026-08-07
- Priority: medium
- Target area: frontend
- Status: **complete**

## Problem
- Rating streak badge shows a number without explanation; users do not know what it means.
- Taste donut legends (genre, director, franchise) can list many rows and overwhelm the stats panel.
- Marathon shelf on the rated tab duplicates passport/gamification content users already see elsewhere.
- Profile «Посты» tab duplicates feed-post browsing already on the global feed; profile should focus on cards and stats.

## Scope
- **Streak explainer:** `RatingStreakBadge` tooltip on tap and desktop hover, mirroring `TasteQuizKnowledgeBadge`; RU copy with pluralization; visibility unchanged (streak > 3).
- **Donut legend collapse:** `StatsDonutChart` gains `legendCollapsedTopN`; pass `8` for genre/director/franchise/decade in `ProfileStatsPanel` and genre/decade in `MonthlyRecapPage`; omit for bounded small-set donuts; «Ещё N» / «Свернуть»; auto-expand when active segment is outside top-N; donut ring stays full data.
- **Rated tab:** remove `MarathonShelfFrame` from `ProfileRatedPanel`; drop marathon props from `ProfilePage` for rated panel only; wrap grid in `ProfileShelfPhysics` when `shelfPhysicsMode` is set; keep passport marathon shelf elsewhere.
- **Remove Posts tab:** remove «Посты» from `ProfileMainTabs` (two tabs: Карточки + Статистика, `grid-cols-2`); narrow `ProfileMainTab` to `'movies' | 'stats'`; strip posts query/panel wiring from `ProfilePage` and `PublicProfilePage` (including `Section header="Посты"` on public profile). Keep `ProfilePostsPanel.tsx`, feed-post API/hooks, and `FeedPage` posts segment — profile-only surface removal.

## Out of scope
- Backend distribution limits or new streak API fields.
- Avatar cloud / bubble animation.
- Deleting `MarathonShelfFrame.tsx` or gamification API.
- Removing feed posts globally (`FeedPage`, post creation, backend list API).
- Profile URL redirect/fallback for posts tab — main tab is local state only; no posts deep-link exists today.

## Acceptance Criteria
- [x] Streak badge shows explainer on tap and on hover (desktop).
- [x] Genre/director/franchise/decade legends (profile stats + monthly recap) show ≤8 rows until expand.
- [x] Rated tab no longer shows marathon list above grid.
- [x] Own profile (`/profile`) and public profile (`/u/:userId`) show only Карточки and Статистика — no «Посты» tab or posts panel.
- [x] Global feed posts on `FeedPage` still work.
- [x] Passport/marathon elsewhere still works.
- [x] Frontend lint/build clean for touched files.

## Design spec
- `docs/superpowers/specs/2026-08-07-profile-streak-stats-legend-ux-design.md`

## Constraints
- Follow existing `TasteQuizKnowledgeBadge` interaction pattern (`button`, `role=tooltip`, `stopPropagation`).
- Preserve API segment order for collapsed legend (first 8 of `visibleSegments`, no client re-sort).
- RU day pluralization via new `formatDaysCount` in `frontend/src/lib/formatRuPlural.ts`.
- Docker-first backend N/A — frontend-only feature.

## Implementation files (Posts tab removal)
| File | Change |
|------|--------|
| `frontend/src/components/profile/ProfileMainTabs.tsx` | Remove posts segment; `ProfileMainTab` → `'movies' \| 'stats'`; `grid-cols-2` |
| `frontend/src/pages/ProfilePage.tsx` | Remove `ProfilePostsPanel` import, posts query/state/render |
| `frontend/src/pages/PublicProfilePage.tsx` | Same + remove `Section header="Посты"` wrapper |
