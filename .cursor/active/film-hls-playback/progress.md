# film-hls-playback — progress

**Status:** ui_shell_only (2026-08-11)

## Current
- Backend playback logic removed (resolvers, service, route, tests, env vars)
- `FilmWatchPage` — UI-заглушка: плеер-плейсхолдер, «Просмотр скоро появится», disabled озвучка/качество
- Кнопка «Смотреть» на странице фильма ведёт на `/films/:id/watch`
- Реализация воспроизведения — в следующих итерациях

## Previously shipped (reverted)
- Kodik/Collaps/Alloha resolvers, `ResolveFilmPlaybackService`, `GET /api/films/{id}/playback`, hls.js player
