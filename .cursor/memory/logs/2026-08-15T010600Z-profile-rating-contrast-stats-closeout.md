# Action log — profile rating contrast stats closeout

- **Timestamp:** 2026-08-15T010600Z
- **Feature slug:** profile-rating-contrast-stats
- **Action type:** closeout
- **Summary:** Profile stats block comparing user ratings to KP/IMDb; fixed API/UI schema mismatch; empty state when passport ratings missing.

## Files

- `backend/src/services/profile/compute_rating_contrast_insights.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/manage_backfill_film_kinopoisk_passport.py`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `docs/features/profile-rating-contrast-stats.md`

## Verification

- `make backend-test-one target=src/tests/unit/services/profile/test_compute_rating_contrast_insights.py`
- `make backend-test-one target=src/tests/integration/api/test_profile_routes.py::test_user_stats_rating_contrast_with_external_ratings`
- `cd frontend && npm run lint && npm run build`
