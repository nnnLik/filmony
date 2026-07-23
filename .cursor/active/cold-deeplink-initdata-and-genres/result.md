# Result — cold-deeplink-initdata-and-genres

**Status:** complete (reconciled with app-hardening-pass AuthProvider merge)

## Implemented

- Cold-start `initData` wait: `WebApp.ready()`, 30 rAF frames, then poll up to 4s @50ms before failing.
- Deeplink navigation only when `auth.kind === 'ready'`; redirect component mounted inside `AuthProvider`.
- Profile poster grid shows `FilmGenreChips` for film genres.

## Coexistence with JWT hardening

- Stored Bearer validated via `GET /api/me` before `ready`; 401 clears token and falls through to Telegram re-auth after initData wait.
- No regressions to backend JWT exp/iat or digest notification code.

## Changed files

- `frontend/src/auth/AuthProvider.tsx`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/profile/MoviePosterGrid.tsx`

## Verification

- `cd frontend && npm run lint -- --max-warnings=0 src/auth/AuthProvider.tsx src/navigation/TelegramMiniAppStartParamRedirect.tsx src/App.tsx` — pass

## Residual risk

- Bearer probe runs before initData wait (intentional fast path); network blip on `/api/me` skips resume and may delay ready until initData path completes.
