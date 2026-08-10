# film-pleer-playback — plan

1. `PleerVideoClient` — GET `{base}/{kinopoisk_id}.json`, parse `embeds[0].iframe`
2. `ResolveFilmPlaybackService` — load film, call client, TTL cache
3. `GET /api/films/{id}/playback` + `FilmPlaybackResponse`
4. Frontend `filmPlaybackApi` + `FilmWatchPage` iframe
5. Tests + docs closeout
