# Watchlist Cards Progress

Status: in_progress

- Added ListUserWatchlistEntriesService with cursor pagination and provider hydration.
- Added GET /api/users/{user_id}/watchlist, presence/delete routes, universal POST /api/me/watchlist.
- Added CreateWatchlistEntryFromCatalogService and rated-card guards on film/catalog create.
- Updated frontend profileApi, CreateCardPage, WatchlistPosterGrid for all providers.
- Extended backend/frontend tests; verification pending.
