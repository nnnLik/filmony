# Plan: followed-content Telegram notifications

1. **Follower resolution:** `ListFollowerUserIdsForFollowingUserService` (`UserSubscription.follower_user_id` where `following_user_id` = author), stable order; optional `exclude_user_ids` for feed-post dedupe.
2. **Delivery:** `NotifyTelegramFollowerNewUserCardService` / `NotifyTelegramFollowerNewFeedPostService` → `deliver_engagement_html_message`; deep links via `html_card_deep_link_block` / `html_feed_post_deep_link_block` from `mini_app_link.py`.
3. **Celery:** tasks `tasks.telegram_engagement.notify_followers_new_user_card` and `notify_followers_new_feed_post` (batch `recipient_user_ids_json`, loop recipients like mention tasks); `telegram_engagement.py` registers helpers.
4. **Routes:** `POST /api/cards` queues follower notify after successful create when follower list non-empty; `POST /api/feed-posts` queues mention tasks first where applicable, then follower notify with `exclude_user_ids`=mention recipients, then bump feed head (order preserved for SSE).
5. **Tests:** card/post happy path; follower list empty skips task; feed post excludes @mention recipients; only-mentioned-followers skips broadcast; service unit tests for list+exclude; HTML copy assertions in `test_follower_publish_telegram_notifications.py`.
6. **Docs & memory:** `docs/features/followed-content-notifications.md`, cross-link from engagement doc, `.cursor/active/…/progress|result.md`, action-log fragment.
