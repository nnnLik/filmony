# Plan: film-kinopoisk-synopsis

Ретроспективный план (реализация уже внесена в репозиторий).

1. Миграция: колонки `film.short_description`, `film.description` (`Text`, nullable).
2. Расширить `KinopoiskFilmPayload` и `KinopoiskClient.get_film` полями из JSON KP.
3. `ResolveKinopoiskFilmService`: запись полей при create/update фильма.
4. API: `FilmResponse`; для карточки — отдельный `MovieCardDetailResponse` + `GetMovieCardDetailsService`.
5. Скрипт бэкфилла с throttling запросов к KP.
6. Фронт: типы, `FilmSynopsisBlock`, вставка в `MovieCardDetailPage`.
7. Pytest: резолв фильма, деталь карточки с синопсисом из БД.
