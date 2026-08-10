# Film watch party (live co-view)

## Scope
Real-time **watch party** while a film plays in-app (`film-pleer-playback`): shared room, presence, chat, invite link, host-led playback sync.

**Not the same as** existing `WatchSession` (watchlist «смотрим вместе» → everyone rates later → feed post). Watch party = **live** session; may **link** to `WatchSession` after party ends (phase 2).

## Acceptance criteria (MVP — phase 1)
- Host creates party from `FilmWatchPage` or film/card detail (**422** if playback unavailable)
- **Any member** can share invite link
- **One active party per user** (409 if already in another room)
- No product cap on roster size (hard max 64 server-side)
- Invite link opens party room (auth required)
- Live presence: who is in the room (online / away / left)
- Room chat (text, rate-limited)
- Host controls: play / pause / seek **state** broadcast to guests
- Guests see sync UI; with pleer iframe — overlay hints + manual «Синхронизироваться» (no cross-origin control)
- Postgres persistence for room metadata + chat history (session lifetime)
- Integration tests for REST; unit tests for sync state machine
- Spec: `docs/superpowers/specs/2026-08-11-film-watch-party-design.md`

## Out of scope (MVP)
- Video bytes proxy on Filmony VPS
- Public unauthenticated rooms
- Voice/video call
- Serial season/episode sync
- Guaranteed sub-second sync inside pleer iframe (requires phase 2 player)

## Depends on
- `film-pleer-playback` (iframe_url resolution)

## Follow-up
- Phase 2: custom `<video>` + hls.js for hard sync
- Phase 3: bridge to `WatchSession` + co-view feed post after party
