# Watchlist Cards

## Summary
Unified «Позже» watchlist for all card providers (Kinopoisk, RAWG, custom activities). Each user owns independent entries; watch-with invites create a second entry for the mutual friend and send a Telegram push.

## Data Model
- Table: `watchlist_entry`
- Fields: `user_id`, `card_id`, `provider_meta`, `watch_tag`, `watch_with_user_id`, `created_at`, `updated_at`
- Unique per user+card: `(user_id, card_id)`

## API

### Create
- `POST /api/me/watchlist` — accepts one of:
  - `film_id` (+ optional `watch_tag`, `watch_with_user_id`)
  - `catalog_item_id` (+ optional `watch_tag`, `watch_with_user_id`)
  - `card_id` + `provider_meta` (+ optional `watch_tag`, `watch_with_user_id`)
- `POST /api/watchlist` — universal create with `card_id`, `provider_meta`, `watch_tag`, optional `watch_with_user_id`

### List
- `GET /api/users/{user_id}/watchlist?cursor&limit` — paginated provider-hydrated list

### Presence / delete
- `GET /api/me/watchlist/presence?card_id=`
- `DELETE /api/me/watchlist/{entry_id}`
- Legacy: `GET/DELETE /api/me/watchlist/films/{film_id}` (Kinopoisk compat)

### Update
- `PATCH /api/watchlist/{entry_id}` — update `watch_tag` (owner only)

## Flows
- **Add to watch-later:** creates entry + feed post (title, description, poster; no rating).
- **Watch with friend:** validates mutual subscription; creates invitee entry; sends Telegram push.
- **Edit:** each user updates only their own entry; no sync between paired entries.

## Frontend
- CreateCardPage step 2: «Только в список «Позже»» with mutual-friend picker and tag chips.
- Profile «Позже» tab: unified poster grid for all providers; delete on own profile.
- Deeplink `w{card_id}` / `watchlist…` opens profile watchlist tab.

## Migration
- `w1x2y3z4a01` — create `watchlist_entry`
- `w1x2y3z4a02` — migrate `user_watchlist_film` → `watchlist_entry`
- `w1x2y3z4a03` — drop `user_watchlist_film`
