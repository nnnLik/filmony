# Result: subscribed-activity-telegram-digest

Status: done

## Implemented
- Telegram digest every 48h for users with subscriptions and Telegram link.
- Scored pool of insights (new cards, feed posts, high ratings, author summaries).
- Weighted random selection of up to 3 items with author/type diversity caps.
- Idempotent digest state per recipient; skip empty windows without spamming.
- Celery batch task with per-recipient error isolation.

## Changed files
- `backend/src/models/subscribed_activity_digest_state.py`
- `backend/src/migrations/versions/x2y3z4a5b678_subscribed_activity_digest_state.py`
- `backend/src/services/subscriptions/list_following_user_ids_for_follower_user.py`
- `backend/src/services/telegram/subscribed_activity_digest_candidates.py`
- `backend/src/services/telegram/list_due_subscribed_activity_digest_recipients.py`
- `backend/src/services/telegram/send_subscribed_activity_digest.py`
- `backend/src/services/telegram/mini_app_link.py`
- `backend/src/tasks/telegram_engagement.py`
- `.cursor/active/subscribed-activity-telegram-digest/progress.md`
- `docs/features/subscribed-activity-telegram-digest.md`

## Verification
- `make backend-test-one target=src/tests/services/telegram/test_subscribed_activity_digest.py` — 6 passed
- `make backend-test-one target=src/tests/tasks/test_subscribed_activity_digest.py` — 3 passed
- `make backend-test-one target=src/tests/services/subscriptions/test_list_following_user_ids_for_follower_user.py` — passed
- `make backend-test-one target=src/tests/test_celery_app.py` — passed
- `docker compose exec backend alembic upgrade head`

## Notes
- Celery beat schedule for the batch task must be configured in deployment (not in repo Celery app yet).
- No new HTTP routes.
- Closeout artifacts now agree on `done` status.
