# watch-party-stale-ttl-404

Hotfix: «Смотреть» stuck on zombie watch party after 12h TTL — 404 `party_not_found`, 409 on recreate, frontend pinned to stale `?party=` slug.

## Root cause

- Prod cron `end_expired_watch_parties` missing → `status=active` past TTL.
- `EnsureActiveWatchPartyService` marked party ended but rolled back on `PartyEnded` HTTP 404.
- Create/join blocked on TTL-expired zombie with 409; frontend did not recover.

## Acceptance

- TTL-expired active party is persisted as `ended` before 404; Redis cleaned up.
- Create/join skip 409 when existing party is TTL-expired; new party allowed.
- Frontend: stale slug 404 → create; 409+404 → retry create once.
- Homelab crontab runs `end_expired_watch_parties` every 15m.
- Backend + frontend tests pass (see result.md).
