# 009 — Telegram notifications

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `telegram-notifications` |
| **Priority** | P2 |
| **Target area** | backend-heavy (+ minimal frontend prefs optional) |
| **Depends on** | [001](./001-telegram-user-base.md), bot token config; **003**/**005**/**008** for event sources |
| **Unlocks** | Engagement loops: friend requests, co-view invites, doppelgänger alerts |

## Summary

Send **outbound messages via Telegram Bot API** for product events: friend request received/accepted, “дооценить” invites, new comments/likes (optional), and **doppelgänger loved a new film** ([`.cursor/user-story.md`](../user-story.md)). Use **Celery** workers for delivery, retries, and rate limiting; bot runs on **webhook** in deployment per [`.cursor/tech.md`](../tech.md).

## Problem

The Mini App is not always open; Telegram notifications pull users back for time-sensitive social and recommendation moments.

## Backend

### Responsibilities

- **Telegram Bot API client**: `sendMessage` with deep link to Mini App start param (e.g. `?startapp=card_123`) where applicable.
- **Event bus / handlers**: subscribe to domain events:
  - Friendship requests (**003**)
  - Co-view invitation (when implemented)
  - Doppelgänger high rating (**008**)
  - Optional: comment mentions (**006**)
- **Idempotency / dedupe**: notification keys in Redis to prevent spam within window.
- **User prefs** (optional v2): mute categories per user stored in DB.
- **Webhook endpoint**: FastAPI route for Telegram updates if processing inline (usually separate from Mini App API or same app with path prefix).

### Configuration

- [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py): `TELEGRAM_BOT_TOKEN`, optional `TELEGRAM_WEBHOOK_URL`, `PUBLIC_APP_BASE_URL` for links.

### Celery

- Tasks: `notify_friend_request`, `notify_doppelganger_pick`, etc.; exponential backoff on `429` / network errors.

### Data

- Log table **`notification_outbox`** optional for audit and retries.

### API (optional)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/me/notifications/settings` | Fetch toggles |
| `PATCH` | `/api/me/notifications/settings` | Update toggles |

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/main.py`](../../backend/src/main.py) | Mount webhook router if colocated |
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | Bot token |

### Suggested new modules

- `backend/src/integrations/telegram/bot_client.py`
- `backend/src/workers/tasks/notifications.py`
- `backend/src/services/notification_service.py`

## Frontend

### Responsibilities

- **Deep links**: ensure Mini App reads `start_param` / `tgWebAppStartParam` and routes to the correct card/profile (coordinate with `@telegram-apps/sdk` usage in [`frontend/src/App.tsx`](../../frontend/src/App.tsx)).
- Optional **settings** screen for notification categories if API exists.

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | Launch params — extend routing based on start param |
| [`frontend/vite.config.ts`](../../frontend/vite.config.ts) | No change required for notifications |

### Suggested new files

- `frontend/src/hooks/useStartParamRoute.ts`
- `frontend/src/pages/NotificationSettingsPage.tsx` (optional)

## Acceptance criteria

- [ ] Test event triggers a Telegram message to the correct `telegram_user_id` in dev/staging bot.
- [ ] Failures in Bot API are retried per Celery policy without duplicate user-visible spam (dedupe).
- [ ] Deep link from notification opens the intended entity in the Mini App.
- [ ] Secrets never logged; webhook verifies Telegram signature if used.

## Out of scope

- Email/push outside Telegram.
- Marketing broadcasts to all users.

## References

- [`.cursor/tech.md`](../tech.md) — Celery, Telegram Bot, webhook deploy.
- [`.cursor/user-story.md`](../user-story.md) — уведомления двойника, приглашения друзей.
- [001](./001-telegram-user-base.md), [003](./003-friends-requests-and-list.md), [008](./008-doppelganger-recommendations.md)
