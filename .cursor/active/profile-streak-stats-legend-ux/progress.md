# profile-streak-stats-legend-ux — progress

Status: **implementation complete** (closeout docs pending)

## 2026-08-07
- Added `formatDaysCount` and streak badge tap/hover tooltip in `RatingStreakBadge.tsx`
- Added `legendCollapsedTopN` to `StatsDonutChart`; wired top-8 collapse in `ProfileStatsPanel` and `MonthlyRecapPage`
- Removed `MarathonShelfFrame` from `ProfileRatedPanel`; dropped marathon props from `ProfilePage`
- Removed «Посты» tab from `ProfileMainTabs`, `ProfilePage`, `PublicProfilePage`
- Verified: `npm run lint` and `npm run build` pass

## Changed files
- `frontend/src/lib/formatRuPlural.ts`
- `frontend/src/components/streaks/RatingStreakBadge.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/pages/MonthlyRecapPage.tsx`
- `frontend/src/components/profile/ProfileRatedPanel.tsx`
- `frontend/src/components/profile/ProfileMainTabs.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
