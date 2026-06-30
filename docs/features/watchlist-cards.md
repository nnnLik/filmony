# Watchlist Cards

## Summary
Unified «Позже» watchlist for all card providers (Kinopoisk, RAWG, custom activities). Each user owns independent entries; watch-with invites create separate entries for each mutual friend and send Telegram pushes.

## Data Model
- Table: `watchlist_entry`
- Fields: `user_id`, `card_id`, `provider_meta`, `watch_tag`, `watch_with_user_id` (legacy primary), `watch_with_user_ids` (JSON array), `created_at`, `updated_at`
- Planned snippet: `user_card.is_planned=true` with `company`, `category_id`, `watch_note`

## API

### Create
- `POST /api/me/watchlist` — accepts one of:
  - `film_id`
  - `catalog_item_id`
  - `card_id` + `provider_meta`
- Optional fields: `watch_tag`, `company`, `category_id`, `watch_note`, `watch_with_user_id` (legacy), `watch_with_user_ids[]` (max 20)
- `POST /api/watchlist` — universal create with same optional fields

### Prefill for rated create
- `GET /api/me/planned-card?card_id=` or `?film_id=` or `?catalog_item_id=` — returns planned card metadata when user rates from «Позже»

### List
- `GET /api/users/{user_id}/watchlist?cursor&limit` — paginated provider-hydrated list (includes `watch_with_user_ids`)

### Presence / delete
- `GET /api/me/watchlist/presence?card_id=`
- `DELETE /api/me/watchlist/{entry_id}`
- Legacy: `GET/DELETE /api/me/watchlist/films/{film_id}` (Kinopoisk compat)

### Update
- `PATCH /api/watchlist/{entry_id}` — update `watch_tag` (owner only)

## Flows
- **Add to watch-later:** wizard step «Детали для «Позже»» → entry + planned card + feed post «Запланировано».
- **Watch with friends:** company ≠ alone → optional multi-select mutual subscriptions; each invitee gets entry + push.
- **Rate later:** create rated card upgrades planned row in place; watchlist entry removed; note/company/shelf pre-filled in wizard.

## Frontend
- CreateCardPage: step 2 preview → «В список «Позже»» opens dedicated details step (company, friends, shelf, note).
- FilmDetailPage: «В список «Позже»» navigates to `/cards/new?filmId=…&branch=watchlist`.
- Profile «Позже» tab: poster grid with «Вместе» badge when invites present.

## Migration
- `w1x2y3z4a01` — create `watchlist_entry`
- `w1x2y3z4a02` — migrate `user_watchlist_film` → `watchlist_entry`
- `w1x2y3z4a03` — drop `user_watchlist_film`
- `w1x2y3z4a04` — `user_card.is_planned`
- `w1x2y3z4a05` — `watchlist_entry.watch_with_user_ids`
