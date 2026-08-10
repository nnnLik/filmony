# Film HLS playback (balancer MVP)

> **Status:** implemented in code; **superseded as primary prod path** by [`film-radarr-playback` spec](../superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md) (Prowlarr + Radarr + qBittorrent + Jellyfin).  
> Balancer env (Kodik/Collaps/Alloha) remains optional behind `PLAYBACK_BALANCER_ENABLED`.

**Radarr rework:**
- Spec: `docs/superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md`
- Prod runbook: `docs/engineering/media-stack-prod-setup.md`

---

## Overview (v1)

Authenticated users watch films inside Filmony via a custom HTML5 `<video>` player. The backend resolves HLS URLs from external balancers by `kinopoisk_id`; video bytes go directly from provider CDN to the client (no Filmony segment proxy).

## User flow
1. Open `/films/:filmId` → tap **Смотреть** (when `kinopoisk_id` is valid)
2. Navigate to `/films/:filmId/watch`
3. Player loads `GET /api/films/{film_id}/playback`
4. Optional translation / quality pickers re-fetch with query params

## API
```
GET /api/films/{film_id}/playback?translation_id=&quality=
Authorization: Bearer or session cookie
```

Responses: `200` with `hls_url`, `qualities`, `translations`, `expires_at`  
Errors: `401`, `404 film_not_found`, `422 playback_unavailable`, `502 playback_provider_error`

## Backend (balancer)
- Provider chain (configured only): Kodik → Collaps → Alloha
- Cache: in-process TTL 600s (`PLAYBACK_CACHE_TTL_SECONDS`)
- Service: `ResolveFilmPlaybackService`

### Env
```
KODIK_API_BASE_URL=
KODIK_TOKEN=
KODIK_LINKHOST=
KODIK_SECRET_TOKEN=
COLLAPS_API_BASE_URL=
COLLAPS_TOKEN=
ALLOHA_API_BASE_URL=
ALLOHA_SECRET=
PLAYBACK_CACHE_TTL_SECONDS=600
```

## Frontend
- `FilmWatchPage` — hls.js on non-iOS, native HLS on iOS/Safari
- Error copy in Russian per design spec

## Out of scope (v1)
- Torrents / WebTorrent
- Segment proxy on Filmony VPS
- Serial season/episode UI
- Continue watching

## Design
- Spec: `docs/superpowers/specs/2026-08-10-film-hls-playback-design.md`
