# Personal digest redesign

Unified weekly and monthly personal digest product: in-app pages, Telegram delivery, and a shared `BuildPersonalDigestService` composer.

**Design spec:** `docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md`

## Products

| Period | In-app | Telegram cron | `period_key` |
|--------|--------|---------------|--------------|
| Week | `/me/digest/week/:periodKey` | Mon 10:00 UTC | `2026-W19` |
| Month | `/me/digest/month/:year/:month` | 1st 10:00 UTC | `2026-05` |

## Backend services

| Service | Role |
|---------|------|
| `BuildPersonalDigestService` | Orchestrates digest DTO for week/month |
| `BuildPersonalDigestFriendsSectionService` | Weekly friends block |
| `BuildPersonalDigestFunFactsService` | Rule-based fun facts + microFun fallback |
| `RenderPersonalDigestTelegramService` | HTML Telegram body |
| `SendPersonalDigestTelegramService` | Idempotent send + `personal_digest_delivery_state` |
| `ListDuePersonalDigestRecipientIdsService` | Eligible recipients per period |

Celery entrypoints: `tasks.personal_digest.send_weekly_personal_digests`, `tasks.personal_digest.send_monthly_personal_digests`.

## Fun facts (Phase 3)

Rule plugins (`genre_dominance`, `rating_all_high`, `rating_wide_spread`, `era_skew`, `collection_sprint`, `marathon_complete`, `new_country_burst`, `streak_record`, `microfun_fallback`) score insights; top **3** (week) or **5** (month) lines are returned with deterministic tie-break on `user_id + period_key`.

MicroFun pools: `digest_weekly`, `digest_monthly` (backend + `frontend/src/lib/microFun/microFunCopy.ts`).

## API

- `GET /api/me/digest/week/{period_key}` / `.../week/latest`
- `GET /api/me/digest/month/{year}/{month}` / `.../month/latest`

Legacy monthly recap routes remain; monthly digest reuses recap aggregation with extended DTO fields.

## Frontend

- `WeeklyDigestPage.tsx` — weekly in-app digest
- `MonthlyRecapPage.tsx` — monthly recap/digest with fun facts section
- Deep links: `wd{period_key}`, `md{year}-{month}` via `mini_app_link.py`

## Legacy pipelines removed

The following standalone Celery pipelines were removed after this redesign (code deleted; DB state tables kept where noted):

- `tasks.monthly_recap.send_monthly_recap_nudges` → `tasks.personal_digest.send_monthly_personal_digests`
- `tasks.telegram_engagement.send_subscribed_activity_digests` (6h subscribed-activity digest)
- `tasks.weekly_controversy.send_weekly_controversy_digests` → controversy block in weekly personal digest

Candidate collectors (`subscribed_activity_digest_candidates.py`, `ComputeWeeklyControversyService`) remain in use inside the weekly digest composer.
