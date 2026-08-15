# Result — profile-rating-contrast-stats

Status: **completed** (2026-08-15T010600Z)

## Implemented

Profile Statistics → Overview block **«Оценки vs КП и IMDb»**:

- Average delta vs Kinopoisk and IMDb
- Agreement % (|Δ| ≤ 1 vs primary source)
- Contrarian count (|Δ| ≥ 4)
- Biggest gap film with link to film/card page

Insight grid on Overview mirrors key metrics when `compared_count > 0`.

## Changed files

- `backend/src/services/profile/compute_rating_contrast_insights.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/manage_backfill_film_kinopoisk_passport.py`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/api/profileTypes.ts`

## Verification

- `make backend-test-one target=src/tests/unit/services/profile/test_compute_rating_contrast_insights.py`
- `make backend-test-one target=src/tests/integration/api/test_profile_routes.py::test_user_stats_rating_contrast_with_external_ratings`
- `cd frontend && npm run lint && npm run build`

## Known limitations

- Metrics require `rating_kinopoisk` / `rating_imdb` on film rows; run KP backfill on prod for full coverage.
- Agreement/contrarian use Kinopoisk deltas when available, else IMDb.

## Next steps

- Monitor prod backfill logs; re-check stats after passport sync completes.
