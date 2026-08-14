# Watch party stale TTL / 404 hotfix

**Closed:** 2026-08-14T221500Z

## Problem

After 12h watch-party TTL, users clicking «Смотреть» got 404 `party_not_found`. A zombie row stayed `active` because prod never ran `end_expired_watch_parties`. Recreate returned 409; GET by slug ran ensure-active, ended the party, but the DB update rolled back on HTTP 404. Frontend stayed on `?party=zombie`.

## Fix

| Layer | Change |
|-------|--------|
| Backend | Commit `ended` + Redis cleanup before `PartyEnded`; create/join ignore TTL-expired zombies |
| Frontend | Stale slug 404 → create; 409+404 → one create retry |
| Ops | Crontab every 15m (see [prod cron](../engineering/prod-cron-filmony.md)) |

## Key code

- `EnsureActiveWatchPartyService`, `CreateWatchPartyService`, `JoinWatchPartyService`
- `useEnsureWatchParty.ts`

## Tests

- `backend/src/tests/integration/services/test_watch_party_v2.py`
- `frontend/src/hooks/__tests__/useEnsureWatchParty.test.tsx`
