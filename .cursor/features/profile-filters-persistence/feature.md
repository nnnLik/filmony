# Profile Filters Persistence

## Goal
Keep profile rated-cards filter selections when the user opens a card and returns to the profile.

## Scope
- Own profile (`/profile`) and public profile (`/users/:userId`) screens.
- All fields in `RatedCardsListQuery`: sort, tags, film title, year range, company, moods, favorites-only, category shelf.
- Persist filters in URL search params so state survives back navigation, reload, and link sharing.

## Acceptance Criteria
- Applying filters updates the profile URL with non-default filter params.
- Opening a card and navigating back restores the same filter UI and list query.
- Reloading a filtered profile URL keeps the filters applied.
- Switching public profile users applies URL filters to the new profile instead of silently resetting to defaults.

## Out of Scope
- Persisting main tab (`movies` / `posts` / `stats`) or watchlist segment in URL.
- Cross-device server-side filter storage.
