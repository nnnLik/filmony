# Синопсис фильма из Кинопоиска (short + full description)

## Цель

Подтягивать с **Kinopoisk API Unofficial** поля `shortDescription` и `description`, **сохранять** их в БД вместе с фильмом, показывать на **странице карточки** (не в общей ленте): сначала краткий текст, по кнопке «Ещё» — полное описание.

## Реализовано

### Данные

- Таблица **`film`**: nullable колонки `short_description`, `description` (`Text`).
- Миграция: `backend/src/migrations/versions/m5n6o7p8q901_film_kinopoisk_descriptions.py`.

### Бэкенд

- **`KinopoiskClient.get_film`**: парсинг JSON `shortDescription` / `description` в `KinopoiskFilmPayload`.
- **`ResolveKinopoiskFilmService`**: при upsert фильма записывает оба поля из ответа KP.
- **`FilmResponse`** (`GET/POST` `/api/films/...`): поля `short_description`, `description` из БД.
- **`MovieCardDetailResponse`** только для **`GET /api/cards/{card_id}`**: `film_short_description`, `film_description`. Элементы **`GET /api/cards/feed`** по-прежнему без синопсиса (меньше JSON и без лишней нагрузки).

### Бэкфилл

- Скрипт: `backend/src/manage_backfill_film_descriptions.py`.
- Запуск в контейнере backend (нужны `DATABASE_URL`, `KINOPOISK_API_KEY`, `KINOPOISK_API_BASE_URL`):

  ```bash
  docker compose exec -w /opt/app backend python src/manage_backfill_film_descriptions.py
  ```

- Флаги: `--dry-run`, `--force`, `--sleep` (пауза между запросами к KP, по умолчанию `0.06`), `--limit N`.
- По умолчанию обрабатываются строки, где **хотя бы одно** из полей `NULL`.

### Фронтенд

- Типы: `Film`, `MovieCard` — опциональные поля синопсиса (для карточки детально).
- Компонент: `frontend/src/components/films/FilmSynopsisBlock.tsx`.
- Подключение: `frontend/src/pages/MovieCardDetailPage.tsx` (под жанрами).

## Проверка

- Pytest (Docker): `make backend-test-one target=src/tests/api/test_cards_routes.py::test_resolve_film_and_get_by_id`, `::test_get_card_includes_film_synopsis`, `::test_resolve_film_series_url`.
- После деплоя: `make migrate`, затем при необходимости скрипт бэкфилла.

## Ограничения и дальше

- Тексты зависят от ответа KP; при ошибке API при резолве карточка фильма всё равно создаётся, поля синопсиса могут остаться пустыми до следующего резолва или бэкфилла.
- При желании можно вынести ленивую догрузку синопсиса без хранения — сейчас выбран путь **хранения в БД** + бэкфилл для уже существующих фильмов.

## Связанные документы

- Базовый резолв фильма по ссылке: [`kinopoisk-movie-by-link.md`](./kinopoisk-movie-by-link.md)
- Исходные материалы фичи: `.cursor/features/film-kinopoisk-synopsis/feature.md`
