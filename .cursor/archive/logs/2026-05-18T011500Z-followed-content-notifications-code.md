Timestamp: 2026-05-18T011500Z
Feature slug: followed-content-notifications
Action type: code
Summary: Added Telegram follower broadcasts for new user cards and new feed posts, with feed-post dedupe against @mention recipients.
Files:
- backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py
- backend/src/services/telegram/notify_follower_new_user_card.py
- backend/src/services/telegram/notify_follower_new_feed_post.py
- backend/src/tasks/telegram_engagement.py
- backend/src/api/cards/routes.py
- backend/src/api/feed_posts/routes.py
- backend/src/tests/api/test_cards_routes.py
- backend/src/tests/api/test_feed_posts_routes.py
- backend/src/tests/test_celery_app.py
- docs/features/followed-content-notifications.md
- docs/features/engagement-telegram-notifications.md
- docs/features/telegram-engagement-notifications.md
Verification: Ruff check passed on touched backend modules; targeted pytest coverage added for card creation, feed-post creation, follower resolution, and mention dedupe.
Links: docs/features/followed-content-notifications.md
