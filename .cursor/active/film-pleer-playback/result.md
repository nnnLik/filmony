# film-pleer-playback — result

**Status:** completed

## Implemented

- `PleerVideoClient` resolves `iframe_url` from `https://pleer.video/{kinopoisk_id}.json`
- `ResolveFilmPlaybackService` with in-process TTL cache (600s default)
- `GET /api/films/{id}/playback` route + `FilmPlaybackResponse` schema
- `FilmWatchPage` iframe player + «Открыть в браузере» for TMA
- `PlaybackSettings` env (`PLAYBACK_ENABLED`, `PLEER_VIDEO_API_BASE_URL`, cache TTL)

## Changed files

- `backend/src/providers/playback/`
- `backend/src/services/films/resolve_film_playback.py`
- `backend/src/api/films/routes.py`, `schemas.py`
- `backend/src/conf/settings.py`
- `backend/src/tests/unit/providers/playback/`
- `backend/src/tests/integration/api/test_film_playback_routes.py`
- `frontend/src/api/filmPlaybackApi.ts`
- `frontend/src/pages/FilmWatchPage.tsx`
- `vars/.env.example`
- `docs/features/film-pleer-playback.md`

## Verification

- `make backend-test-one target=src/tests/unit/providers/playback/test_pleer_video_client.py` — 4 passed
- `make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py` — 4 passed
- `cd frontend && npm run lint && npm run build` — OK

## Known limitations

- pleer.video third-party embed; not all Kinopoisk ids covered
- iframe in Telegram Mini App may require external browser
- Watch-together deferred
