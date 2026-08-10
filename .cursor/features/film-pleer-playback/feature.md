# Film playback via pleer.video (iframe)

## Scope
In-app film watch for authenticated users via **pleer.video** embed by `kinopoisk_id`. No partner API tokens. Filmony backend resolves `iframe_url`; client embeds iframe (video bytes stay on pleer.video CDN).

## Acceptance criteria
- `GET /api/films/{id}/playback` returns `iframe_url` when pleer.video has the title
- `FilmWatchPage` shows fullscreen iframe + «Открыть в браузере» fallback for TMA
- «Смотреть» CTA on `FilmDetailPage` when `kinopoisk_id >= 1`
- Unit tests for pleer client parsing; integration tests for route (mocked upstream)
- Docs in `docs/features/film-pleer-playback.md`

## Out of scope
- Custom `<video>` / hls.js
- Watch-together sync
- Serial season/episode UI
