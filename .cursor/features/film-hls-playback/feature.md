# Film HLS playback

## Scope
- In-app HLS playback for films with `kinopoisk_id` via custom `<video>` (no iframe, no segment proxy on Filmony VPS).
- Backend resolves stream URLs from external balancers (Kodik → Collaps → Alloha).
- Frontend watch page `/films/:filmId/watch` + «Смотреть» CTA on film detail.

## Acceptance criteria
- `GET /api/films/{film_id}/playback` (auth) returns HLS metadata or 404/422/502 per spec.
- Unit tests for resolvers; integration tests for route auth and error paths.
- `FilmWatchPage` with hls.js (non-iOS) / native HLS (iOS).
- `make backend-test-one` for playback tests; `npm run lint && npm run build`.

## Out of scope (MVP)
- Torrents / WebTorrent / Jackett
- Filmony HLS segment proxy
- Serial season/episode UI
- Continue watching / progress sync
