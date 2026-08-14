# Plan — tma-watch-open-browser

1. Add `frontend/src/lib/openFilmWatchInBrowser.ts`: detect TMA, show confirm, on OK call `WebApp.openLink` with `${origin}/films/{id}/watch`; otherwise navigate in-app.
2. Wire «Смотреть» `onClick` on `FilmDetailPage` and `MovieCardDetailPage`.
3. Add `frontend/src/lib/__tests__/openFilmWatchInBrowser.test.ts` (TMA confirm/open, cancel, non-TMA).
4. Closeout: feature artifacts, HOT, action-log.
