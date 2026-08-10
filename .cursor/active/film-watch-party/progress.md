# film-watch-party — progress

**Status:** completed (MVP + v2)

## Done
- MVP 1a–1d (initial ship)
- v2 UX-0: unified `/films/:id/watch` (solo = party), redirect `/watch-party/:slug`
- v2 UX-1: simplified sheets, chat dedup, fixed input
- v2 backend: Redis SSE/chat/RL/presence, Celery expire, typing, watching batch, invites, WatchSession bridge
- v2 frontend: SSE reconnect, drift banner, virtual chat, watching badge, invite sheet, end bridge sheet

## Verification
- `docker compose exec -T backend uv run pytest -n0 --no-cov src/tests/unit/services/watch_parties/ src/tests/integration/api/test_watch_party_routes.py src/tests/integration/api/test_watch_party_sse_routes.py src/tests/integration/services/test_watch_party_v2.py` — 20 passed
- `cd frontend && npm run lint && npm run build` — pass (1 TanStack Virtual compiler warning)
- `npm run test -- --run src/lib/__tests__/mergeWatchPartyMessages.test.ts` — 3 passed
