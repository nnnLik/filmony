# Result: profile-stats-director-franchise

Status: completed

## Implemented

- Extended `GetUserCardStatsService` with director/franchise distribution and insights.
- API schemas updated for new response fields.
- Profile stats Overview: insight cards for favorite director/series, unique directors in metric strip.
- Profile stats Taste: director and franchise donut charts with drill-down to rated cards.
- Link «Все режиссёры →» on director donut section.

## Changed files

- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/lib/statsDonutChart.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

## Verification

- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_director_and_franchise_distribution` — pass
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_aggregates` — pass
- `cd frontend && npm run lint && npm run build` — pass

## Known limitations

- No average rating per director/franchise in distribution (V2).
- No franchises index page link.
- Marathon cross-links to Collection tab not added.
