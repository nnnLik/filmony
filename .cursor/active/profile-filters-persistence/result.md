# Profile Filters Persistence — Result

Status: completed

## Implemented
- Profile rated-cards filters are serialized to URL search params (non-default values only).
- `ProfilePage` and `PublicProfilePage` hydrate and sync filter state through `useRatedCardsQueryFromUrl`.
- Returning from a card detail route restores filters from the profile URL in browser history.

## Changed Files
- `frontend/src/lib/ratedCardsListQuery.ts`
- `frontend/src/lib/__tests__/ratedCardsListQuery.test.ts`
- `frontend/src/hooks/useRatedCardsQueryFromUrl.ts`
- `frontend/src/hooks/__tests__/useRatedCardsQueryFromUrl.test.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Verification
- `cd frontend && npm test -- ratedCardsListQuery useRatedCardsQueryFromUrl` — 9 tests passed
- `cd frontend && npm run lint` — passed
- `cd frontend && npm run build` — passed

## Limitations / Next Steps
- Main profile tab and watchlist/rated segment are not stored in the URL.
- Filter param order in the URL is not stable (semantically equivalent URLs may differ in string form).
