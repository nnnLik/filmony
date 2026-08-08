# personal-digest-redesign — plan

Spec: [docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md](../../../docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md)

## Phase 0 — Spec + cron shell (current)

- [x] Design spec
- [x] Celery task registration (batch stub until Phase 1)
- [x] Prod crontab swap (2 digest crons)

## Phase 1 — Monthly

- [ ] `personal_digest_delivery_state` migration
- [ ] Extend monthly builder (actors, collections, achievements, streak)
- [ ] Monthly Telegram teaser + evolve MonthlyRecapPage
- [ ] Deprecate `send_monthly_recap_nudges` cron usage

## Phase 2 — Weekly

- [ ] `BuildPersonalDigestFriendsSectionService`
- [ ] Weekly page + Telegram render
- [ ] Controversy as optional weekly insight

## Phase 3 — Fun facts + cleanup

- [ ] Insight rules + microFun pools
- [ ] Remove deprecated cron docs; optional state table migration
