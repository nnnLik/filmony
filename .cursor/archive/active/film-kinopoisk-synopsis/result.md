# Result: film-kinopoisk-synopsis

## Что сделано

Синопсис из Кинопоиска (`shortDescription` → `short_description`, `description` → `description`) сохраняется в БД при резолве фильма, отдаётся в `FilmResponse` и только в **`GET /api/cards/{id}`** (тип `MovieCardDetailResponse`). Лента карточек без этих полей. Скрипт бэкфилла для уже существующих строк `film`. На UI — компонент с «Ещё» / «Свернуть».

## Изменённые файлы (основные)

- `backend/src/models/film.py`
- `backend/src/migrations/versions/m5n6o7p8q901_film_kinopoisk_descriptions.py`
- `backend/src/services/kinopoisk/client.py`
- `backend/src/services/kinopoisk/resolve_kinopoisk_film.py`
- `backend/src/api/films/schemas.py`, `backend/src/api/films/routes.py`
- `backend/src/api/cards/schemas.py`, `backend/src/api/cards/routes.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/manage_backfill_film_descriptions.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/films/FilmSynopsisBlock.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`

## Проверка

- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_resolve_film_and_get_by_id`
- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_get_card_includes_film_synopsis`
- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_resolve_film_series_url`
- `make migrate` перед бэкфиллом на окружении с БД.

## Ограничения

См. [`docs/features/film-kinopoisk-synopsis.md`](../../../docs/features/film-kinopoisk-synopsis.md).
