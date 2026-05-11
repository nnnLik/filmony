# Film Kinopoisk synopsis (short + full description)

| Field | Value |
|--------|--------|
| **Feature slug** | `film-kinopoisk-synopsis` |
| **Target area** | fullstack |
| **Depends on** | Kinopoisk resolve / `film` entity ([`kinopoisk-movie-by-link`](../../../docs/features/kinopoisk-movie-by-link.md)) |

## Summary

Добавить к сущности фильма текстовый синопсис из **Kinopoisk API Unofficial** (`shortDescription`, `description`): сохранение в PostgreSQL, отдача в API фильма и в **детальном** ответе карточки; в ленте не отдавать. UI: краткий текст + «Ещё» / «Свернуть» для полного описания.

## Acceptance criteria (выполнено)

1. При резолве по URL KP поля синопсиса попадают в БД (`film.short_description`, `film.description`).
2. `FilmResponse` содержит `short_description` и `description` (из БД).
3. `GET /api/cards/{id}` содержит `film_short_description` и `film_description`; `GET /api/cards/feed` — без этих полей.
4. Скрипт проходит по существующим фильмам и дозаполняет поля из KP (с паузой под rate limit).
5. На странице карточки фильма отображается блок синопсиса с раскрытием.

## Итоговая документация

- [`docs/features/film-kinopoisk-synopsis.md`](../../../docs/features/film-kinopoisk-synopsis.md)
