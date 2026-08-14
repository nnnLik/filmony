# Action log — watch UX + social + provider slices closeout

- **Timestamp:** 2026-08-15T024800Z
- **Feature slug:** watch-ux-social-provider-slices (umbrella)
- **Action type:** closeout
- **Summary:** Shipped P0–P2 watch/social slices and KP/TMDB passport block on film detail.

## Changed areas

- Watch leave rate prompt: `frontend/src/lib/watchLeaveRatePrompt.ts`, `frontend/src/pages/FilmWatchPage.tsx`
- TMA same room: `frontend/src/lib/openFilmWatchInBrowser.ts`
- Playback unavailable: `backend/src/services/films/resolve_film_playback.py`, `frontend/src/components/watchparty/PlaybackUnavailableState.tsx`
- Card following ratings: `frontend/src/pages/MovieCardDetailPage.tsx`, `FollowingRatingsPanel.tsx`
- Evening for two: `backend/src/services/watchlist/pick_evening_for_two_film.py`, `frontend/src/components/watchlist/EveningForTwoSection.tsx`
- Watching now vitrine: `backend/src/services/watch_parties/list_following_watching_now.py`, `frontend/src/components/watchparty/WatchingNowVitrineSection.tsx`
- Provider catalog: `backend/src/migrations/versions/h6i7j8k9l012_film_passport_fields.py`, `backend/src/api/films/mappers.py`, `backend/src/providers/tmdb/tmdb_snapshot_*.py`, `frontend/src/components/films/FilmPassportRow.tsx`

## Verification

- `make backend-test-one target=src/tests/integration/api/test_evening_for_two_routes.py` — 3 passed
- `make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py` — 5 passed
- `make backend-test-one target=src/tests/unit/providers/tmdb/` — 7 passed
- `cd frontend && npm run lint && npm run build` — OK (1 pre-existing warning)
- Frontend vitest slices — 16+ passed

## Docs

- `docs/features/watch-ux-social-provider-slices.md`
