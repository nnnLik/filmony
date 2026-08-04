# Action Log Entry

- Timestamp: 2026-07-03T192800Z
- Feature slug: subscribed-activity-telegram-digest
- Action type: code
- Summary: Implemented Telegram digest for subscribed activity (48h cadence, scored pool, Celery batch task, digest state model).
- Files:
  - backend/src/models/subscribed_activity_digest_state.py
  - backend/src/migrations/versions/x2y3z4a5b678_subscribed_activity_digest_state.py
  - backend/src/services/subscriptions/list_following_user_ids_for_follower_user.py
  - backend/src/services/telegram/subscribed_activity_digest_candidates.py
  - backend/src/services/telegram/list_due_subscribed_activity_digest_recipients.py
  - backend/src/services/telegram/send_subscribed_activity_digest.py
  - backend/src/services/telegram/mini_app_link.py
  - backend/src/tasks/telegram_engagement.py
- Verification: `make backend-test-one target=src/tests/services/telegram/test_subscribed_activity_digest.py`; `docker compose exec backend alembic upgrade head`
