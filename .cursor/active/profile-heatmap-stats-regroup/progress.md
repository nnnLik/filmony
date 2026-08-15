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
