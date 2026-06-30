# Watchlist Cards

## Scope
- Replace legacy user_watchlist_film with provider-aware watchlist entries.
- Add watchlist create/update API with card_id + provider_meta payloads.
- Create feed posts on watchlist add and send invite notifications.
- Migrate legacy watchlist data to the new model.

## Acceptance Criteria
- Watchlist entries store card_id and provider_meta per user.
- Watchlist add creates a feed post.
- Watch-with invites create an independent entry and send Telegram push.
- Legacy user_watchlist_film is migrated and no longer used by services or routes.
