# Subscribed Activity Telegram Digest

## Status
done

## Summary
Backend-only Telegram digest for subscribed activity. It gathers recent signals from followed users, builds a scored pool, selects up to 3 diverse insights, and sends the result through the existing Telegram delivery path.

The feature uses per-recipient digest state for idempotency, skips empty or low-quality windows, and keeps recipient-level failures isolated in the Celery batch task. No new HTTP routes were added.

## Verification
- `make backend-test-one target=src/tests/services/telegram/test_subscribed_activity_digest.py` - 6 passed
- `make backend-test-one target=src/tests/tasks/test_subscribed_activity_digest.py` - 3 passed
- `make backend-test-one target=src/tests/services/subscriptions/test_list_following_user_ids_for_follower_user.py` - passed
- `make backend-test-one target=src/tests/test_celery_app.py` - passed
- `docker compose exec backend alembic upgrade head`

## Notes
- Celery beat scheduling for the batch task is configured in deployment.
- Existing follower publish notifications and other Telegram delivery flows remain unchanged.
