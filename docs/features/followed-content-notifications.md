# Follower notifications on publish (Telegram)

## Summary

When a user **creates a movie/game user card** or **publishes a feed post**, each **follower** (subscriber) of that author receives a **Telegram direct message** if they have linked Telegram (`telegram_user_id`). Delivery is **asynchronous via Celery**; API responses are unchanged on Telegram failures.

**Feed-post rule:** recipients who already get the **post @mention** notification for the same publish event are **excluded** from the follower broadcast (no duplicate DM).

Manual **share card** (`POST /api/cards/{id}/share`) and all existing mention / comment / reaction notifications are unchanged.

## Celery tasks

| Task name | Trigger |
|-----------|---------|
| `tasks.telegram_engagement.notify_followers_new_user_card` | `POST /api/cards` success, follower list non-empty |
| `tasks.telegram_engagement.notify_followers_new_feed_post` | `POST /api/feed-posts` success, followers minus `@mention` set non-empty |

Arguments: `actor_user_id` (str UUID), content id (`card_id` / `feed_post_id`), `recipient_user_ids_json` (JSON array of UUID strings).

## Notification copy (HTML, `parse_mode=HTML`)

Placeholders below: `{Actor}` = escaped display name/slug fallback; `{URL}` = `https://t.me/<bot_username>/app?startapp=…` when `TELEGRAM_BOT_USERNAME` is set, else the plaintext fallback from `mini_app_link` helpers.

### New user card — follower DM

Rendered structure (literal line breaks):

```text
📽 <b>{Actor}</b> опубликовал(а) новую карточку

{Title line}

{Deep link line}
```

- **Title line** — if linked to `Film`: `🎬 «{Film.title}»` and ` ({year})` when year exists. If no film (e.g. game card): `🎬 «{display_title or "Карточка"}»`.
- **Deep link line:** `🔗 <a href="{URL}?startapp=c{card_id}">Открыть в Filmony</a>` or the non-link fallback “Откройте приложение Filmony из Telegram” when bot username is unset.

Implementation: [`notify_follower_new_user_card.py`](../../backend/src/services/telegram/notify_follower_new_user_card.py).

### New feed post — follower DM

```text
✨ <b>{Actor}</b> опубликовал(а) пост в ленте

📝 <i>«{snippet}»</i>

{Deep link line}
```

- **Snippet:** post `body` with inline tokens `⟦…⟧` stripped, whitespace collapsed; max **160** characters + `…` if truncated. If empty after stripping: `📝 <i>(без текста)</i>` (still italic).
- **Deep link line:** `🔗 <a href="{URL}?startapp=p{post_id}">Открыть пост в ленте</a>` or the same plaintext fallback.

Implementation: [`notify_follower_new_feed_post.py`](../../backend/src/services/telegram/notify_follower_new_feed_post.py).

Contrast with **mention DM** (`notify_feed_post_mention.py`): `📣 Вас упомянули в посте ленты` + actor + snippet — follower broadcast intentionally uses **publish** wording and `✨` header.

## Related code

- [`list_follower_user_ids_for_following_user.py`](../../backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py) — follower UUIDs + optional exclusions.
- [`telegram_engagement.py`](../../backend/src/tasks/telegram_engagement.py) — task registration.
- [`engagement-telegram-notifications.md`](./engagement-telegram-notifications.md) — other engagement DM types.

## Feature metadata

- Request: `.cursor/features/followed-content-notifications/feature.md`
