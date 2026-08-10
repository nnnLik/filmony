# film-hls-playback — result

**Status:** completed  
**Closed:** 2026-08-10

## Implemented
- Pluggable playback resolvers: Kodik, Collaps, Alloha (configured via env)
- `ResolveFilmPlaybackService` with 10 min in-memory cache and provider chain
- `GET /api/films/{film_id}/playback` (auth required)
- Frontend `FilmWatchPage` at `/films/:filmId/watch` with native HLS (iOS) / hls.js
- «Смотреть» CTA on `FilmDetailPage` when `kinopoisk_id >= 1`

## Changed files
- `backend/src/providers/playback/*`
- `backend/src/services/films/resolve_film_playback.py`
- `backend/src/api/films/routes.py`, `schemas.py`
- `backend/src/conf/settings.py`
- `backend/src/tests/unit/providers/playback/*`
- `backend/src/tests/integration/api/test_film_playback_routes.py`
- `frontend/src/pages/FilmWatchPage.tsx`
- `frontend/src/api/filmPlaybackApi.ts`
- `frontend/src/lib/hlsPlayer.ts`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/routes.tsx`
- `frontend/package.json`
- `vars/.env.example`

## Verification
```bash
make backend-test-one target=src/tests/unit/providers/playback/
make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py
cd frontend && npm run lint && npm run build
```
All passed.

## Manual beta checklist
- [ ] Set `KODIK_*` / `COLLAPS_*` / `ALLOHA_*` env on backend
- [ ] iOS TMA: inline HLS play on `/films/:id/watch`
- [ ] Desktop: hls.js playback, translation/quality pickers
- [ ] 422 when no provider configured / no source

## Known limitations
- No Filmony segment proxy — CDN hotlink may fail (user switches quality/provider)
- Torrent/WebTorrent fallback deferred
- Movies-only (no serial episode UI)

## Next steps
- Add magnet/WebTorrent fallback phase
- Optional Redis cache if multi-replica backend
