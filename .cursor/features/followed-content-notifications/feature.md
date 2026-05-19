# Followed-content Telegram notifications

## Scope

- When a user creates a **new user card** or **new feed post**, enqueue Telegram DMs for every **follower** of the author (`UserSubscription`: `following_user_id` = author, `following_user_id` excluded from recipients).
- **Telegram only** (no in-app inbox).
- **Feed posts:** followers who already receive the post’s **@mention** notification must **not** get a second “new post” follower notification (exclude `mentioned_user_ids` from the follower broadcast list).
- Preserve existing mention notifications, manual card share (`deliver_shared_movie_card`), comment/reaction flows, and feed bumping.

## Acceptance criteria

- [x] Card creation enqueues Celery work for all followers with `telegram_user_id` (delivery still skips if no chat, per existing patterns).
- [x] Feed post creation enqueues follower broadcast excluding mention recipients; mention task unchanged.
- [x] Notification copy documented; deep links use `html_card_deep_link_block` / `html_feed_post_deep_link_block` (Mini App `startapp`).
- [x] Thin routes: follower resolution in `ListFollowerUserIdsForFollowingUserService`; delivery in dedicated Telegram notify services + Celery tasks.
- [x] Pytest covers happy paths, no-followers skip, and mention/follower dedupe.

## Out of scope

- Email/push/in-app notifications.
- Batching rate limits beyond existing Celery/task patterns.
