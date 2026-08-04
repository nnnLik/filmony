# Action Log Entry

- **Timestamp:** 2026-07-23T13:16:00Z
- **Feature slug:** profile-later-tab-back-nav
- **Action type:** code

## Summary
Fixed profile back navigation after opening a card from the «Позже» (watchlist) tab: the movies segment now persists in the URL (`?movies=watchlist`) via `profileMoviesSegment` helpers and `useProfileMoviesSegmentFromUrl`, so browser back returns to «Позже» instead of defaulting to «Оценённые».

## Files
- `frontend/src/lib/profileMoviesSegment.ts`
- `frontend/src/hooks/useProfileMoviesSegmentFromUrl.ts`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/components/create/WatchlistForm.tsx`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `frontend/src/lib/__tests__/profileMoviesSegment.test.ts`
- `frontend/src/hooks/__tests__/useProfileMoviesSegmentFromUrl.test.tsx`

## Verification
- `cd frontend && npm test -- profileMoviesSegment useProfileMoviesSegmentFromUrl` — 6 passed
- `cd frontend && npm run lint` — passed
