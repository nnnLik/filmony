# Film watch party (live co-view)

Live **watch party** rooms while a film plays via pleer.video: invite link, roster, chat, host-led playback state (soft sync).

Distinct from **WatchSession** (async watchlist «смотрим вместе» → ratings → feed post).

## User flow
1. Host taps **«Смотреть вместе»** on watch/film/card pages → party created (422 if playback unavailable).
2. Host lands on `/watch-party/:inviteSlug` with iframe + host controls.
3. Guests open invite link → join → see sync banner + chat.
4. Host play/pause/seek updates SSE for all members; guests use **«Синхронизироваться»** for manual iframe alignment.
5. Host **«Завершить сеанс»** or leave ends room; TTL 12h.

## API (auth required)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/watch-parties` | `{ film_id }` |
| GET | `/api/watch-parties/by-slug/{invite_slug}` | Resolve slug |
| GET | `/api/watch-parties/{id}` | Snapshot |
| POST | `/api/watch-parties/{id}/join` | 409 if already active elsewhere |
| POST | `/api/watch-parties/{id}/leave` | Host leave ends party |
| POST | `/api/watch-parties/{id}/end` | Host only |
| POST | `/api/watch-parties/{id}/kick` | Host only |
| POST | `/api/watch-parties/{id}/playback` | Host: play/pause/seek |
| GET/POST | `/api/watch-parties/{id}/messages` | Chat |
| POST | `/api/watch-parties/{id}/heartbeat` | Presence (30s client interval) |
| GET | `/api/watch-parties/{id}/events` | SSE |

## Env
- `WATCH_PARTY_HARD_MAX_MEMBERS` (default 64)
- `WATCH_PARTY_MAX_ACTIVE_PER_USER` (default 1)
- `WATCH_PARTY_TTL_HOURS` (default 12)
- `WATCH_PARTY_SSE_PING_SECONDS` (default 25)
- `PUBLIC_APP_BASE_URL` (invite URLs)

## Telegram
- Deep link: `startapp=wp{invite_slug}` → `/watch-party/{slug}`

## Deferred
- Hard sync with owned player (HLS)
- Post-party `WatchSession` bridge
- Redis SSE fan-out for multi-worker

Spec: [docs/superpowers/specs/2026-08-11-film-watch-party-design.md](../superpowers/specs/2026-08-11-film-watch-party-design.md)
