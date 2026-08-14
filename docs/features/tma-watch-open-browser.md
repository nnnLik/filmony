# TMA watch opens system browser

In Telegram Mini App, tapping «Смотреть» shows a native confirm: «Вы будете перенаправлены в браузер для просмотра фильма.» OK opens `${origin}/films/{id}/watch` via `WebApp.openLink` (system browser). Cancel stays in the Mini App. Outside TMA, watch stays in-app.

Helper: `frontend/src/lib/openFilmWatchInBrowser.ts`. Wired from `FilmDetailPage` and `MovieCardDetailPage`.
