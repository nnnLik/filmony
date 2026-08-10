# Film watch party (live co-view)

Live **watch party** rooms while a film plays via pleer.video: invite link, roster, ephemeral chat, host-led playback state (soft sync).

Distinct from **WatchSession** (async watchlist «смотрим вместе» → ratings → feed post).

## User flow
1. User taps **«Смотреть»** on film/card pages → party auto-created (solo = 1-member room, same UI).
2. Lands on `/films/:filmId/watch` with iframe; optional chat / invite / roster in header.
3. Guests open invite link (`/watch-party/:slug` or Telegram `wp{slug}`) → redirect to watch page with `?party=slug`.
4. Host play/pause/seek updates SSE; guests see drift banner + **«Синхронизироваться»** for manual iframe alignment.
5. Host **«Завершить»** may opt into **«Оценить вместе»** → `WatchSession` bridge.
6. Chat is **ephemeral** (Redis, lost on reload); party TTL 12h.

## API (auth required)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/watch-parties` | `{ film_id }` |
| POST | `/api/watch-parties/watching/batch` | `{ user_ids }` — global «сейчас смотрит» badge |
| GET | `/api/watch-parties/by-slug/{invite_slug}` | Resolve slug |
| GET | `/api/watch-parties/{id}` | Snapshot |
| POST | `/api/watch-parties/{id}/join` | 409 if already active elsewhere |
| POST | `/api/watch-parties/{id}/leave` | Host leave ends party |
| POST | `/api/watch-parties/{id}/end` | Host only |
| POST | `/api/watch-parties/{id}/kick` | Host only |
| POST | `/api/watch-parties/{id}/playback` | Host: play/pause/seek |
| GET/POST | `/api/watch-parties/{id}/messages` | Ephemeral chat (`before_id` cursor) |
| POST | `/api/watch-parties/{id}/typing` | Typing indicator |
| POST | `/api/watch-parties/{id}/invite` | `{ user_ids }` mutual-follow Telegram invite |
| POST | `/api/watch-parties/{id}/bridge-watch-session` | Host opt-in → WatchSession |
| POST | `/api/watch-parties/{id}/heartbeat` | Presence (30s client interval) |
| GET | `/api/watch-parties/{id}/events` | SSE (`?since_seq=` reconnect) |

## Env
- `WATCH_PARTY_HARD_MAX_MEMBERS` (default 64)
- `WATCH_PARTY_MAX_ACTIVE_PER_USER` (default 1)
- `WATCH_PARTY_TTL_HOURS` (default 12)
- `WATCH_PARTY_SSE_PING_SECONDS` (default 25)
- `WATCH_PARTY_REDIS_URL` (fallback `CATALOG_CACHE_REDIS_URL` → `CELERY_BROKER_URL`)
- `WATCH_PARTY_CHAT_MAX_MESSAGES` (default 200)
- `WATCH_PARTY_HEARTBEAT_INTERVAL_SECONDS` (default 30)
- `WATCH_PARTY_MISSED_HEARTBEATS_AWAY` (default 3)
- `WATCH_PARTY_MISSED_HEARTBEATS_LEFT` (default 20)
- `PUBLIC_APP_BASE_URL` (invite URLs)

## Infrastructure
- SSE fan-out via Redis pub/sub (in-memory fake in `ENV=test`)
- Ephemeral chat in Redis LIST (no `watch_party_message` table)
- Celery `end_expired_watch_parties` every 15 min (see `docs/engineering/prod-cron-filmony.md`)

## Telegram
- Deep link: `startapp=wp{invite_slug}` → `/watch-party/{slug}` → `/films/:id/watch?party=slug`

## Deferred
- Hard sync with owned player (HLS)

Spec: [docs/superpowers/specs/2026-08-11-film-watch-party-design.md](../superpowers/specs/2026-08-11-film-watch-party-design.md)
