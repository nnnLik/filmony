# Action log — film-pleer-playback closeout

- **Timestamp:** 2026-08-11T005500Z
- **Feature slug:** film-pleer-playback
- **Action type:** closeout

## Summary

Implemented in-app film watch via pleer.video iframe embed (no partner API token). Backend resolves `iframe_url` by `kinopoisk_id`; frontend shows iframe on `FilmWatchPage` with external browser fallback for TMA.

## Files

- `backend/src/providers/playback/pleer_video_client.py`
- `backend/src/services/films/resolve_film_playback.py`
- `backend/src/api/films/routes.py`
- `backend/src/api/films/schemas.py`
- `backend/src/conf/settings.py`
- `backend/src/tests/unit/providers/playback/test_pleer_video_client.py`
- `backend/src/tests/integration/api/test_film_playback_routes.py`
- `frontend/src/api/filmPlaybackApi.ts`
- `frontend/src/pages/FilmWatchPage.tsx`
- `docs/features/film-pleer-playback.md`

## Verification

- `make backend-test-one target=src/tests/unit/providers/playback/test_pleer_video_client.py` — 4 passed
- `make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py` — 4 passed
- `cd frontend && npm run lint && npm run build` — OK
