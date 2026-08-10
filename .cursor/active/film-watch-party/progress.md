# film-watch-party — progress

**Status:** completed (MVP 1a–1d)

## Done
- Phase 1a: models, migration, settings, core REST + integration tests
- Phase 1b: SSE broker, playback/chat/heartbeat + unit/integration tests
- Phase 1c: WatchPartyPage, SSE hook, soft-sync UI, chat/roster/share
- Phase 1d: entry CTAs, create sheet, `wp_` deep link, docs

## Verification
- `docker compose exec -T backend uv run pytest -n0 --no-cov src/tests/integration/api/test_watch_party_routes.py src/tests/integration/api/test_watch_party_sse_routes.py src/tests/unit/services/watch_parties/`
- `cd frontend && npm run lint && npm run build`
- `npm run test -- --run src/lib/__tests__/miniAppCardDeepLink.test.ts`
