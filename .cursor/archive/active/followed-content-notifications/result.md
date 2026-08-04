# Result: followed-content notifications

## Implemented

- Added automatic Telegram follower notifications for **new user cards** and **new feed posts**.
- Added a follower-resolution service that reads `UserSubscription` rows from the author to all followers, with optional exclusions for feed-post mention recipients.
- Kept the API layer thin: routes enqueue Celery work after successful create operations.
- Feed-post notifications now avoid duplicate broadcasts for users already covered by `@mentions`.

## Files changed

- `backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py`
- `backend/src/services/telegram/notify_follower_new_user_card.py`
- `backend/src/services/telegram/notify_follower_new_feed_post.py`
- `backend/src/tasks/telegram_engagement.py`
- `backend/src/api/cards/routes.py`
- `backend/src/api/feed_posts/routes.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/tests/api/test_feed_posts_routes.py`
- `backend/src/tests/test_celery_app.py`
- `docs/features/followed-content-notifications.md`
- `docs/features/engagement-telegram-notifications.md`
- `docs/features/telegram-engagement-notifications.md`
- `.cursor/features/followed-content-notifications/feature.md`
- `.cursor/active/followed-content-notifications/plan.md`
- `.cursor/active/followed-content-notifications/progress.md`
- `.cursor/active/followed-content-notifications/result.md`
- `.cursor/memory/logs/2026-05-18T011500Z-followed-content-notifications-code.md`
- `.cursor/memory/logs/action-log.md`

## Verification

- `uv run ruff check src/services/subscriptions/list_follower_user_ids_for_following_user.py src/services/telegram/notify_follower_new_user_card.py src/services/telegram/notify_follower_new_feed_post.py src/tasks/telegram_engagement.py src/api/cards/routes.py src/api/feed_posts/routes.py src/tests/api/test_cards_routes.py src/tests/api/test_feed_posts_routes.py src/tests/test_celery_app.py`
- `make backend-test-one target=src/tests/test_celery_app.py`
- `docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/api/test_cards_routes.py::test_create_card_queues_follower_publish_notify src/tests/api/test_cards_routes.py::test_create_card_no_followers_skips_follower_notify src/tests/api/test_feed_posts_routes.py::test_feed_post_create_queues_follower_publish_notify src/tests/api/test_feed_posts_routes.py::test_feed_post_follower_notify_excludes_mention_recipients src/tests/api/test_feed_posts_routes.py::test_feed_post_only_followers_mentioned_skips_follower_broadcast src/tests/api/test_feed_posts_routes.py::test_feed_post_create_no_followers_skips_follower_notify -q`

## Limitations

- Telegram-only; no in-app inbox for this feature.
