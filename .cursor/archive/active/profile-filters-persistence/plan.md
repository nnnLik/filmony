# Profile Filters Persistence — Plan

Status: completed

## Approach
1. Add URL serialization helpers for `RatedCardsListQuery`.
2. Introduce `useRatedCardsQueryFromUrl` hook to hydrate from and sync to search params.
3. Replace page-local filter state in `ProfilePage` and `PublicProfilePage`.
4. Add unit/integration tests for serialization and back-navigation restore.
5. Run frontend lint/build/tests and publish delivery docs.

## Notes
- Card detail back navigation uses browser history (`navigate(-1)`); URL-backed filters restore on profile remount without changing `MovieCardDetailPage`.
