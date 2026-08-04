# Action log — profile-activity-heatmap (2026-07-03)

| Timestamp (UTC) | Feature | Action | Summary | Files |
|-----------------|---------|--------|---------|-------|
| 2026-07-03T19:40:00Z | profile-activity-heatmap | implement | Backend: `completed_at`, stats activity buckets, `completed_on` list filter | `backend/src/models/user_card.py`, `backend/src/migrations/versions/y3z4a5b6c789_user_card_completed_at.py`, `backend/src/services/profile/get_user_card_stats.py`, `backend/src/services/profile/list_user_cards.py`, `backend/src/api/profile/users_routes.py` |
| 2026-07-03T19:45:00Z | profile-activity-heatmap | test | Backend pytest for heatmap exclusion, shelf filter, completed_on | `backend/src/tests/api/test_profile_routes.py` — `make backend-test-one` PASS |
| 2026-07-03T19:50:00Z | profile-activity-heatmap | implement | Frontend heatmap component + stats panel integration | `frontend/src/components/profile/ProfileActivityHeatmap.tsx`, `frontend/src/components/profile/ProfileStatsPanel.tsx`, `frontend/src/lib/activityHeatmapGrid.ts` |
| 2026-07-03T19:52:00Z | profile-activity-heatmap | implement | URL/query `completedOn` for drill-down | `frontend/src/lib/ratedCardsListQuery.ts`, `frontend/src/api/profileApi.ts` |
| 2026-07-03T19:55:00Z | profile-activity-heatmap | test | Frontend lint/build/vitest | `npm run lint`, `npm run build`, vitest — PASS |
| 2026-07-03T19:58:00Z | profile-activity-heatmap | docs | Feature docs and delivery artifacts | `docs/features/profile-activity-heatmap.md`, `.cursor/active/profile-activity-heatmap/result.md` |
