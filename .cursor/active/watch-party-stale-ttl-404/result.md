# Result — watch-party-stale-ttl-404

Status: **completed** (2026-08-14T221500Z)

## Implemented

- TTL-expired parties end persistently (no rollback on 404); Redis keys cleared.
- Create/join no longer 409 on zombie TTL-expired row.
- Frontend recovers from stale `?party=` slug via create / retry.
- Prod cron: `*/15 * * * *` `end_expired_watch_parties` on homelab.

## Changed files

- `backend/src/daos/watch_party_dao.py`
- `backend/src/services/watch_parties/ensure_active_watch_party.py`
- `backend/src/services/watch_parties/create_watch_party.py`
- `backend/src/services/watch_parties/join_watch_party.py`
- `backend/src/tests/integration/services/test_watch_party_v2.py`
- `frontend/src/hooks/useEnsureWatchParty.ts`
- `frontend/src/hooks/__tests__/useEnsureWatchParty.test.tsx`
- `docs/engineering/prod-cron-filmony.md`

## Verification

- `make backend-test-one target=src/tests/integration/services/test_watch_party_v2.py` → 5 passed
- `cd frontend && npm run lint` → ok
- `cd frontend && npx vitest run src/hooks/__tests__/useEnsureWatchParty.test.tsx` → 3/3 passed

## Limitations

Cron lives on homelab only; doc must stay accurate to avoid recurrence.
