# tma-watch-open-browser

In Telegram Mini App, «Смотреть» must confirm before leaving the WebView, then open the film watch URL in the system browser. Standalone browser keeps in-app navigation.

## Acceptance

- TMA: native confirm «Вы будете перенаправлены в браузер для просмотра фильма.» with OK/Cancel.
- OK opens `${origin}/films/{id}/watch` via `WebApp.openLink`.
- Cancel stays in the Mini App.
- Non-TMA (standalone browser): unchanged in-app watch.
- Vitest covers the helper (`openFilmWatchInBrowser`).
