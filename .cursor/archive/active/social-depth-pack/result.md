# Social Depth Pack — result

**Status:** complete

## Implemented

### Slice A — Watchlist overlap
- `GET /api/me/watchlist/overlaps` + `ListWatchlistOverlapsService`
- Profile «Ещё хотят посмотреть», film/card banners, confirm sheet + prefill watch-with

### Slice B — Co-view → post
- `watch_session` model + migration
- Session on watch-with create; rating progress on planned→rated
- `CreateCoViewFeedPostService`, `co_view_splits` in feed (global + legacy paths)
- Celery finalize + Telegram nudge

### Slice C — Weekly controversy
- `weekly_controversy_state` + compute/get services
- `GET /api/me/weekly-controversy`, Celery digest task, FilmDetailPage chip

### Slice D — Rating streak badge
- `POST /api/streaks/batch`, `GET /api/me/streak`
- `RatingStreakBadge` with heat animation on all nick surfaces (≥4 days)

## Changed files (high level)

**Backend:** `services/watchlist/list_watchlist_overlaps.py`, `services/watch_sessions/*`, `services/controversy/*`, `services/streaks/*`, `api/profile/me_routes.py`, `api/streaks/`, `api/controversy/`, migrations, `tasks/watch_session.py`, `tasks/weekly_controversy.py`

**Frontend:** `WatchlistOverlapSection`, `WatchTogetherConfirmSheet`, `CoViewSplitRatings`, `RatingStreakBadge`, streak/overlap/controversy API clients, wired into feed/profile/search surfaces

### Slice C — Weekly controversy (Telegram upgrade)
- `WeeklyControversyBundle` with runner-up, polar cards, avg/year, viewer rating
- Film deeplink `startapp=f{id}` + frontend redirect
- Rich TG HTML + inline button; spread≥4 send gate; `link_card_id` in state

## Verification (2026-07-29 upgrade)

- `make backend-test-one target=src/tests/services/test_build_weekly_controversy_message.py` — 6 passed
- `make backend-test-one target=src/tests/api/test_weekly_controversy_routes.py` — 9 passed
- `make backend-test-one target=src/tests/services/test_mini_app_link.py` — 6 passed
- `alembic upgrade head` in Docker — `e6f7a8b90123`
- `cd frontend && npm run lint` — pass

## Verification (initial)

## Known limitations

- Celery beat for weekly controversy not in docker-compose (deployment-only, like digest)
- Co-view session has no accept/decline UI
- Streak uses UTC day boundaries only
