## 2026-05-25T20:12:00Z — profile-and-public-profiles — code

- Summary: Lazy-load shelf catalog for profile rated filters (and stats extra filters): no `GET .../card-categories` until the user expands the shelf UI; React Query longer `staleTime`/`gcTime`; sessionStorage placeholder + clear on auth reset (mirrors movie tag stats pattern).

- Feature slug: `profile-and-public-profiles`

- Action type: `code`

### Files

- `frontend/src/lib/userCardCategoriesStorage.ts`
- `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/components/profile/ProfileStatsFilters.tsx`
- `frontend/src/auth/AuthProvider.tsx`

### Verification

- `cd frontend && npm run lint && npm run build`
- `cd frontend && npm test -- --run`
