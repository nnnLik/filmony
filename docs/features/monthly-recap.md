# Monthly Recap

Monthly in-app summary of rated-card activity. Telegram delivery has moved to the **personal digest** pipeline.

See also: [Personal digest redesign](personal-digest-redesign.md) and the design spec at `docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md`.

## API

Legacy recap routes (still supported):

- `GET /api/me/recap/{year}/{month}` — auth required, own recap only (UTC month boundaries).
- `GET /api/me/recap/latest` — previous complete calendar month.

Preferred monthly digest routes (same payload shape, richer fields):

- `GET /api/me/digest/month/{year}/{month}`
- `GET /api/me/digest/month/latest` — alias of recap latest

Response includes overview stats, people, taste breakdowns, gamification unlocks, collection deltas, achievements, streak, and `fun_facts`.

## Telegram

Monthly recap teasers are delivered via the **personal digest** pipeline: `tasks.personal_digest.send_monthly_personal_digests` (prod cron: 1st day 10:00 UTC). Short HTML teaser + deep link `startapp=md{year}-{month}`.

Idempotency: `personal_digest_delivery_state (user_id, period, period_key)`.

## Frontend

- Legacy: `/me/recap/:year/:month` and `/me/recap/latest` (`MonthlyRecapPage.tsx`)
- Digest: `/me/digest/month/:year/:month` and `/me/digest/month/latest`
- Profile banner when latest month has ratings; dismiss via `localStorage` key `recap_dismissed_{y}_{m}`.
