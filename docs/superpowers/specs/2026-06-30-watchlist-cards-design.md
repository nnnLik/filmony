## Overview
Define a unified watchlist and feed card experience using ProviderMeta
(Card + ProviderMeta) for all media types. Extend watchlist support to
non-kinopoisk cards (RAWG games, custom activities) while keeping user
entries independent and minimizing legacy cleanup.

## Goals
- Support watchlist entries for non-kinopoisk cards (RAWG games, custom
  activities) using the Card + ProviderMeta shape.
- Always create a feed post when a user adds a card to watch-later.
- Allow selecting a mutual friend to watch with, using a fixed
  `watch_tag` enum and explicit `watch_with_user_id`.
- Create independent watchlist entries for both users when a watch-with
  invite is set, and notify the invited user via Telegram push.
- Migrate legacy `user_watchlist_film` data to the new abstract
  watchlist model and remove the old model and API.

## Non-goals
- Broad refactors of watchlist-related code or unrelated feed systems.
- Synchronizing or auto-updating watchlist entries between users.
- Expanding feed post content beyond the approved watch-later payload.

## Data model
- Abstract watchlist entry model supports Card + ProviderMeta across
  providers (kinopoisk, RAWG, custom activity).
- Fields include: `user_id`, `card_id`, `provider_meta`, `watch_tag`,
  `watch_with_user_id`, `created_at`, `updated_at`.
- `watch_tag` uses a fixed enum for watch-later semantics.
- Each user owns their own entry; entries are not linked beyond the
  invite action.

## API changes
- Watchlist create supports provider-aware Card + ProviderMeta payload.
- Watchlist create accepts `watch_tag` and optional `watch_with_user_id`
  for mutual watch selection.
- Legacy `user_watchlist_film` API is removed after migration.

## Flows
- **Add to watch-later**: create watchlist entry for the actor user and
  always create a feed post with title, description, poster, comments,
  and emotions; exclude personal rating/details.
- **Watch with friend**: when `watch_with_user_id` is supplied, create
  a second watchlist entry for the invited user using the same card
  payload and `watch_tag`.
- **Edit watchlist entry**: each user can update only their own entry;
  no synchronization between paired entries.

## Notifications
- When `watch_with_user_id` is set, send a Telegram push notification to
  the invited user describing the watch-with invitation and linking to
  the watchlist entry/card.

## Migration and legacy cleanup
- Migrate all `user_watchlist_film` records into the new abstract
  watchlist model, preserving user ownership and timestamps where
  available.
- Remove the legacy model and API endpoints after migration.
- Perform minimal cleanup: rename or correct clearly incorrect legacy
  field names if encountered; avoid unrelated refactors.

## Acceptance criteria
- Watchlist entries support non-kinopoisk cards via Card + ProviderMeta.
- Adding to watch-later always creates a feed post with the approved
  content scope (title, description, poster, comments, emotions only).
- Watch-with invites create independent entries for both users and send
  a Telegram push to the invited user.
- Users can edit only their own watchlist entries without sync.
- Legacy `user_watchlist_film` data is migrated, and old model/API are
  removed with minimal cleanup.
