# personal-digest-redesign

## Scope

Replace fragmented Telegram digests with **2 personal products**: weekly (detailed + friends + fun facts) and monthly (full stats teaser + rich in-app). Unified `BuildPersonalDigestService`, 2 prod crons.

## Acceptance criteria

- [ ] Spec approved: `docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md`
- [ ] Prod crontab: weekly Mon 10 UTC + monthly 1st 10 UTC
- [ ] Celery tasks `send_weekly_personal_digests`, `send_monthly_personal_digests`
- [ ] Weekly: personal + friends block + fun facts (Telegram + in-app)
- [ ] Monthly: extended stats (actors, collections, achievements) + Telegram teaser
- [ ] Old digest crons removed from prod
- [ ] pytest coverage for digest pipeline

## Spec

`docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md`
