# Watchlist Cards Progress

Status: complete

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
