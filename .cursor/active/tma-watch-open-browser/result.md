# Result — tma-watch-open-browser

Status: **completed** (2026-08-14T221500Z)

## Implemented

TMA «Смотреть» shows native confirm, then opens `${origin}/films/{id}/watch` in the system browser via `WebApp.openLink`. Cancel stays. Standalone browser keeps in-app watch.

## Changed files

- `frontend/src/lib/openFilmWatchInBrowser.ts`
- `frontend/src/lib/__tests__/openFilmWatchInBrowser.test.ts`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`

## Verification

Placeholder (fill after runs):

- `cd frontend && npx vitest run src/lib/__tests__/openFilmWatchInBrowser.test.ts`
- `cd frontend && npm run lint`

## Limitations

None in scope. Backend / watch-party files untouched.
