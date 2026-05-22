## Implemented

- **Frontend:** `CreateCardPage` remix bootstrap uses `catalog_game` when template has `provider === 'rawg'` and a positive `catalog_item_id`, preserving shared catalog anchor for POST `/api/cards`. Kinopoisk/film and manual paths unchanged.
- **Backend:** Two new async API tests for `GET /api/cards/{id}/following-ratings` with RAWG `catalog_item_id` matching (list + `viewer_rating`).

## Files changed

- `frontend/src/pages/CreateCardPage.tsx`
- `backend/src/tests/api/test_following_ratings_for_movie_card.py`
- `docs/features/movie-card-following-ratings.md`
- `.cursor/active/rawg-card-linking/*`, `.cursor/memory/logs/*`

## Verification

- Frontend: `cd frontend && npm run lint && npm run build` — pass
- Backend: `docker exec -w /opt/app filmony-backend pytest src/tests/api/test_following_ratings_for_movie_card.py -v` — 6 passed

## Limitations

- Makefile `backend-test-one` uses `docker exec -it`, which can fail in non-TTY environments; direct `docker exec` without `-it` works for CI-style runs.

## Next steps

- None required for this slice.
