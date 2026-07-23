# Action log

- **Timestamp:** 2026-07-23T16:16:00Z
- **Feature slug:** cold-deeplink-initdata-and-genres
- **Action type:** code
- **Summary:** Cold-start initData polling (rAF + up to 4s @50ms), WebApp.ready(), deeplink redirect gated on auth ready inside AuthProvider, profile poster genre chips.
- **Files:**
  - `frontend/src/auth/AuthProvider.tsx`
  - `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/components/profile/MoviePosterGrid.tsx`
- **Verification:** `cd frontend && npm run lint -- --max-warnings=0 src/auth/AuthProvider.tsx src/navigation/TelegramMiniAppStartParamRedirect.tsx src/App.tsx` (exit 0)
