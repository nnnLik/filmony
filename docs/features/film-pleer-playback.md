# Film playback via pleer.video

## Overview

Authenticated users watch films in-app via **pleer.video iframe embed**. Backend resolves `iframe_url` by `kinopoisk_id`; video bytes never pass through Filmony VPS.

## User flow

1. `/films/:filmId` → **Смотреть** (when `kinopoisk_id >= 1`)
2. `/films/:filmId/watch` → `GET /api/films/{id}/playback`
3. Full-width iframe + **Открыть в браузере** (Telegram Mini App fallback)

## API

```
GET /api/films/{film_id}/playback
Authorization: Bearer or session cookie
```

**200:** `{ provider, title, iframe_url, film_id, kinopoisk_id, expires_at }`  
**401** unauthenticated · **404** `film_not_found` · **422** `playback_unavailable` · **502** `playback_provider_error`

## Backend

- `PleerVideoClient` — `GET {PLEER_VIDEO_API_BASE_URL}/{kinopoisk_id}.json`
- `ResolveFilmPlaybackService` — film lookup + in-process TTL cache
- No partner API token required

### Env

```
PLAYBACK_ENABLED=true
PLEER_VIDEO_API_BASE_URL=https://pleer.video
PLAYBACK_CACHE_TTL_SECONDS=600
```

## Frontend

- `FilmWatchPage` — iframe embed
- `filmPlaybackApi.ts` — playback fetch

## Limitations

- pleer.video availability varies by title
- iframe may be blocked inside Telegram Mini App — use external browser button
- Third-party player UI (not custom `<video>`)

## Tests

- `backend/src/tests/unit/providers/playback/test_pleer_video_client.py`
- `backend/src/tests/integration/api/test_film_playback_routes.py`

Run: `make backend-test-one target=src/tests/unit/providers/playback/test_pleer_video_client.py`
