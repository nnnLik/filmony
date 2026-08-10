# film-watch-party — result

**Status:** completed (MVP)

## Implemented
- Live watch party domain (`WatchParty`, `WatchPartyMember`, `WatchPartyMessage`) separate from async `WatchSession`
- REST: create/join/get/by-slug/leave/end/kick, playback, chat, heartbeat
- In-process SSE broker with snapshot + playback/chat/presence/party_ended events
- Soft sync: host controls + guest sync hints (pleer iframe, no cross-origin control)
- `WatchPartyPage` with iframe, roster, chat sheet, invite copy, host countdown
- Entry CTAs on `FilmWatchPage`, `FilmDetailPage`, `MovieCardDetailPage`
- Telegram deep link `wp{slug}` / `wp_{slug}` → `/watch-party/:inviteSlug`

## Changed files (high level)
- Backend: `models/watch_party*.py`, `daos/watch_party_dao.py`, `services/watch_parties/*`, `api/watch_parties/*`, migration `f4a5b6c7d890_watch_party.py`, settings
- Frontend: `pages/WatchPartyPage.tsx`, `api/watchParty*.ts`, `lib/watchPartySse.ts`, `hooks/useWatchParty*.tsx`, `components/watchparty/WatchPartyCreateSheet.tsx`, routes, miniAppCardDeepLink
- Tests: `test_watch_party_routes.py`, `test_watch_party_sse_routes.py`, unit broker/playback tests, deep link vitest

## Verification
```bash
docker compose exec -T backend uv run pytest -n0 --no-cov \
  src/tests/integration/api/test_watch_party_routes.py \
  src/tests/integration/api/test_watch_party_sse_routes.py \
  src/tests/unit/services/watch_parties/
cd frontend && npm run lint && npm run build
npm run test -- --run src/lib/__tests__/miniAppCardDeepLink.test.ts
```
All passed locally after backend container restart.

## Known limitations
- SSE broker is single-worker (same as global feed MVP)
- No hard video sync inside pleer iframe (phase 2)
- No bridge to `WatchSession` after party end (phase 3)
- In-app mutual-follow push invite not implemented (copy link + TMA deep link only)

## Next steps
- Phase 2: custom `<video>` + HLS hard sync
- Phase 3: end party → spawn/link `WatchSession` for co-rating feed post
