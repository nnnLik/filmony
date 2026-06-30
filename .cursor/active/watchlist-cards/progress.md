# Watchlist Cards Progress

Status: complete

## Watchlist wizard details (2026-06-30)
- Extended watchlist create API: `company`, `category_id`, `watch_note`, `watch_with_user_ids[]`.
- Migration `w1x2y3z4a05`: JSONB `watchlist_entry.watch_with_user_ids`.
- Planned card stores company/shelf/note; upsert updates existing planned rows.
- Rated create upgrades planned card in place (preserves feed snippet id + note carryover).
- `GET /api/me/planned-card` for prefill when rating from «Позже».
- Frontend: dedicated wizard step «Детали для «Позже»» (company, multi-friends, shelf, note).
- FilmDetailPage «Позже» opens create wizard with `branch=watchlist`.

## Completion phase (2026-06-30)
- Added mutual watch partner validation (`AssertMutualWatchPartnerService`) for watch-with invites.
- Forwarded `watch_tag` and `watch_with_user_id` through film/catalog create shims.
- Replaced placeholder watchlist feed posts with title/description/poster snapshot from `provider_meta`.
- Added migration `w1x2y3z4a03` to drop legacy `user_watchlist_film` table.
- Frontend: mutual-friend picker, watch tag chips, profile watchlist delete/edit wiring, FilmDetailPage universal API, invite deeplinks.

## Earlier milestones
- Added ListUserWatchlistEntriesService with cursor pagination and provider hydration.
- Added GET /api/users/{user_id}/watchlist, presence/delete routes, universal POST /api/me/watchlist.
- Added CreateWatchlistEntryFromCatalogService and rated-card guards on film/catalog create.
- Updated frontend profileApi, CreateCardPage, WatchlistPosterGrid for all providers.
- Renamed fixtures to user_card/card_comment/card_tag; fixed fixtures-load.
