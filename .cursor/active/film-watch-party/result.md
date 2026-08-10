# film-watch-party — result (v2)

**Status:** completed

## Implemented (v2)
- Unified watch UX: one «Смотреть» CTA, `/films/:id/watch` for solo and group; `/watch-party/:slug` redirects
- Simplified UI: header + iframe + sheets (roster, chat, host controls, end/bridge, invite)
- Ephemeral Redis chat (drop `watch_party_message`); pagination + virtual scroll
- Redis SSE fan-out, seek/message rate limits, user_watching presence keys
- Heartbeat away/left via missed-heartbeat settings
- SSE reconnect with `since_seq`; guest drift banner
- Typing indicator; global «сейчас смотрит» badge (batch API + feed/profile wiring)
- Mutual-follow in-app invite + Telegram notification
- Host opt-in bridge party → WatchSession (`source_watch_party_id`)
- Celery `end_expired_watch_parties` (cron */15)

## Key files
- Backend: `watch_party_redis.py`, refactored broker/messages/heartbeat, `end_expired_watch_parties.py`, invite/bridge/batch/typing services, migration `g5h6i7j8k901_watch_party_v2_redis_bridge.py`
- Frontend: `FilmWatchPage.tsx`, `WatchPartyRedirectPage.tsx`, `components/watchparty/*`, `useEnsureWatchParty.ts`, `mergeWatchPartyMessages.ts`, watching badge hooks

## Verification
```bash
docker compose exec -T backend uv run pytest -n0 --no-cov \
  src/tests/unit/services/watch_parties/ \
  src/tests/integration/api/test_watch_party_routes.py \
  src/tests/integration/api/test_watch_party_sse_routes.py \
  src/tests/integration/services/test_watch_party_v2.py
cd frontend && npm run lint && npm run build
npm run test -- --run src/lib/__tests__/mergeWatchPartyMessages.test.ts
```
20 backend tests passed; frontend lint/build pass.

## Known limitations
- Soft sync only (pleer iframe); hard sync deferred
- Chat lost on page reload (by design)
- TanStack Virtual triggers React Compiler incompatible-library warning (expected)
