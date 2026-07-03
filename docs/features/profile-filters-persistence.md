# Profile Filters Persistence

## Goal
Preserve profile rated-cards filter selections when opening a card and returning to the profile, including after page reload or when opening a shared link.

## Behavior
- Filter changes update the profile URL query string with only non-default values.
- Supported params: `sort`, `tags`, `filmTitle`, `yearMin`, `yearMax`, `company`, `moodBefore`, `moodAfter`, `favoritesOnly`, `categoryId`.
- Opening `/cards/:id` from a filtered profile and pressing back restores the filtered profile URL from history.
- Both own profile (`/profile`) and public profile routes use the same hook-backed state.

## Key Components
- `frontend/src/lib/ratedCardsListQuery.ts` — query model plus URL parse/serialize helpers.
- `frontend/src/hooks/useRatedCardsQueryFromUrl.ts` — two-way sync between React state and `location.search`.
- `frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/PublicProfilePage.tsx` — consumers of the hook.

## Testing
- `frontend/src/lib/__tests__/ratedCardsListQuery.test.ts` — round-trip and merge behavior.
- `frontend/src/hooks/__tests__/useRatedCardsQueryFromUrl.test.tsx` — hydration, URL writes, remount, and card back navigation.

Run:
```bash
cd frontend && npm test -- ratedCardsListQuery useRatedCardsQueryFromUrl
cd frontend && npm run lint && npm run build
```

## Limitations
- Profile main tab and movies/watchlist segment are not persisted in the URL.
- Invalid URL values fall back to filter defaults.
