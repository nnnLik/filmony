# Plan — watch-party-stale-ttl-404

Status: **done** (hotfix shipped 2026-08-14T221500Z)

1. **Backend persist** — `EnsureActiveWatchPartyService`: commit status + Redis cleanup before raising `PartyEnded`; add `WatchPartyDAO.commit()`.
2. **Backend unblock** — `CreateWatchPartyService` / `JoinWatchPartyService`: treat TTL-expired active party as absent (no 409).
3. **Frontend recovery** — `useEnsureWatchParty`: 404 on stale slug → create; 409 then 404 → single create retry.
4. **Tests** — extend `test_watch_party_v2.py`; add `useEnsureWatchParty.test.tsx`.
5. **Ops** — install homelab crontab; document full `docker exec` line in `prod-cron-filmony.md`.
