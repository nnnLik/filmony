# Closeout: film-hls-playback

- **Timestamp:** 2026-08-10T224800Z
- **Feature slug:** film-hls-playback
- **Action type:** closeout
- **Summary:** In-app HLS playback MVP — backend resolver chain (Kodik/Collaps/Alloha), playback API, watch page with hls.js, «Смотреть» CTA.

## Files
- `backend/src/providers/playback/`
- `backend/src/services/films/resolve_film_playback.py`
- `backend/src/api/films/routes.py`
- `backend/src/api/films/schemas.py`
- `backend/src/conf/settings.py`
- `backend/src/tests/unit/providers/playback/`
- `backend/src/tests/integration/api/test_film_playback_routes.py`
- `frontend/src/pages/FilmWatchPage.tsx`
- `frontend/src/api/filmPlaybackApi.ts`
- `frontend/src/lib/hlsPlayer.ts`
- `docs/features/film-hls-playback.md`

## Verification
- `make backend-test-one target=src/tests/unit/providers/playback/` — 9 passed
- `make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py` — 6 passed
- `cd frontend && npm run lint && npm run build` — pass
