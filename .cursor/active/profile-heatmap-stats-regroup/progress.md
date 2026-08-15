# Progress Log

## Feature
- Slug: profile-heatmap-stats-regroup
- Status: in_progress

## Plan (brief)
- Move activity heatmap from Statistics (`ProfileStatsPanel`) onto the main profile surface.
- Collapse stats sub-tabs to three RU labels: **Обзор**, **Вкус**, **Сообщество**.
- Redistribute every existing analytics block into the new tab layout — no data dropped.
- Keep heatmap out of stats tab / `ProfileStatsPanel` entirely.

## Action Entries
### 2026-08-15 01:16
- Action type: kickoff
- Summary: Registered feature in HOT; created progress log; starting feature.md, plan.md, and frontend implementation.
- Files:
  - `.cursor/HOT.md`
  - `.cursor/active/profile-heatmap-stats-regroup/progress.md`
- Verification:
  - n/a (kickoff)
- Notes:
  - HOT updated: `profile-heatmap-stats-regroup` added as in_progress item 1.

### 2026-08-15
- Action type: implementation
- Summary: Shrunk heatmap to last 30 days (last month); backend `HEATMAP_WINDOW_DAYS=30` for `activity_start`/`activity_end`/`activity_distribution`; `activity_total_180d` insight unchanged (180-day rollup); frontend `clipHeatmapWindow` + copy «за последний месяц».
- Files:
  - `backend/src/services/profile/get_user_card_stats.py`
  - `backend/src/tests/integration/api/test_profile_routes.py`
  - `frontend/src/lib/activityHeatmapGrid.ts`
  - `frontend/src/lib/__tests__/activityHeatmapGrid.test.ts`
  - `frontend/src/components/profile/ProfileActivityHeatmap.tsx`
- Verification:
  - `clipHeatmapWindow` unit tests; profile stats integration asserts 29-day heatmap span
- Notes:
  - Stats insight **За 6 месяцев** still driven by `activity_total_180d`.

### 2026-08-15
- Action type: refactor
- Summary: Cut extra heatmap category fetch; share stats query cache with the stats tab; hide redundant single-shelf chips; fetch shelf metadata only on Вкус.
- Files:
  - `frontend/src/components/profile/ProfileActivityHeatmapSection.tsx`
  - `frontend/src/components/profile/ProfileActivityHeatmap.tsx`
  - `frontend/src/components/profile/ProfileStatsPanel.tsx`
  - `frontend/src/components/profile/ProfileStatsTab.tsx`
  - `frontend/src/pages/ProfilePage.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
- Verification:
  - `cd frontend && npm run lint` exit 0 (pre-existing WatchPartyChatList warning only)
  - `npx vitest run src/lib/__tests__/activityHeatmapGrid.test.ts` 4/4
  - `cd frontend && npm run build` exit 0
  - heatmap integration tests 2 passed (`make backend-test-one` both activity heatmap cases)
  - ruff `get_user_card_stats.py` clean
- Notes:
  - Stats service stays O(1) queries vs card count (batched actors + franchise labels; grouped activity). No N+1.

### 2026-08-15
- Action type: perf
- Summary: Slim `GET /activity-heatmap` for profile chrome; sessionStorage 5min placeholder; invalidate profile aggregates on card create/update/delete; full `/stats` only when the stats tab mounts.
- Files:
  - `backend/src/services/profile/user_card_activity.py`
  - `backend/src/services/profile/get_user_activity_heatmap.py`
  - `backend/src/api/profile/users_routes.py`
  - `frontend/src/hooks/useUserActivityHeatmapQuery.ts`
  - `frontend/src/lib/activityHeatmapCache.ts`
  - `frontend/src/lib/invalidateProfileAggregates.ts`
  - `frontend/src/components/profile/ProfileActivityHeatmapSection.tsx`
- Verification:
  - frontend lint/build + authBootstrap + heatmap grid tests
  - 4 heatmap integration tests passed
  - ruff on new heatmap modules
- Notes:
  - Opening profile no longer downloads full stats JSON.

### 2026-08-15 ~01:45
- Action type: code
- Summary: Removed heatmap shelves; hover count; compact card; compact subscribe/guess/invite buttons.
- Files:
  - `frontend/src/components/profile/ProfileActivityHeatmap.tsx`
  - `frontend/src/components/profile/ProfileActivityHeatmapSection.tsx`
  - `frontend/src/pages/ProfilePage.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
- Verification:
  - `cd frontend && npx eslint src/components/profile/ProfileActivityHeatmap.tsx src/components/profile/ProfileActivityHeatmapSection.tsx src/pages/ProfilePage.tsx src/pages/PublicProfilePage.tsx` exit 0
  - `npx vitest run src/lib/__tests__/activityHeatmapGrid.test.ts` 4/4
