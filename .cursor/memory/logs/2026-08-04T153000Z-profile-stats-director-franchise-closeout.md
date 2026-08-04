# Action log — profile-stats-director-franchise closeout

- **Timestamp:** 2026-08-04T153000Z
- **Feature slug:** profile-stats-director-franchise
- **Action type:** closeout

## Summary

Added director and franchise aggregates to profile stats API and UI (Overview insights + Taste donuts with drill-down).

## Files

- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/lib/statsDonutChart.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `docs/features/profile-stats-director-franchise.md`

## Verification

- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_director_and_franchise_distribution`
- `cd frontend && npm run lint && npm run build`
