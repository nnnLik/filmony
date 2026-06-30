# Watchlist Cards

## Summary
- Watchlist entries now store provider-aware `card_id` plus `provider_meta`.
- Watchlist add creates a feed post and optional invite notification.
- Legacy `user_watchlist_film` data is migrated to the new table.

## API
- POST `/api/watchlist` accepts `card_id`, `provider_meta`, `watch_tag`, optional `watch_with_user_id`.
- PATCH `/api/watchlist/{entry_id}` updates `watch_tag` for the owner.

## Data Model
- `watchlist_entry` replaces `user_watchlist_film` for storing watchlist entries.
