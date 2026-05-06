---
name: kinopoisk_card_metadata
overview: "Расширить создание карточки фильма и структуру Film данными из Kinopoisk API: добавить `genres` и прокинуть `kinopoisk_id + genres` в контракт `POST /api/cards` и ответы карточек."
todos:
  - id: db-film-genres
    content: Добавить поле genres в Film + Alembic миграцию
    status: completed
  - id: kinopoisk-parse-genres
    content: Расширить Kinopoisk client и resolve service для genres
    status: completed
  - id: cards-contract
    content: Обновить CardCreateRequest/CreateMovieCardInput и валидацию kinopoisk_id+genres
    status: completed
  - id: cards-read-dto
    content: Протащить film_kinopoisk_id/film_genres в детали карточки и список профиля
    status: completed
  - id: frontend-payload
    content: Обновить фронтенд-типы и payload createMovieCard
    status: completed
  - id: tests
    content: Обновить/добавить API-тесты для новых полей и валидации
    status: completed
isProject: false
---

# План: расширение карточки и структуры фильма (Kinopoisk metadata)

## Цель
Сделать создание карточки фильма богаче и устойчивее: хранить `genres` в сущности фильма (как `string[]`), принимать `kinopoisk_id` и `genres` в `POST /api/cards`, валидировать согласованность с `film_id`, и возвращать эти поля в DTO карточек.

## Что меняем
- **Модель фильма и БД**
  - Добавить поле `genres` в [backend/src/models/film.py](backend/src/models/film.py) (тип хранения: массив строк / JSON-массив строк в PostgreSQL).
  - Создать миграцию в [backend/src/migrations/versions](backend/src/migrations/versions) для нового столбца `film.genres` с безопасным дефолтом (`[]`/`NULL` + нормализация в коде).
- **Интеграция с Kinopoisk API**
  - Расширить payload клиента в [backend/src/services/kinopoisk/client.py](backend/src/services/kinopoisk/client.py): парсить `genres` из ответа `GET /films/{id}` (`Genre[]`, поле `genre`).
  - Обновить сервис резолва в [backend/src/services/kinopoisk/resolve_kinopoisk_film.py](backend/src/services/kinopoisk/resolve_kinopoisk_film.py), чтобы при создании/обновлении фильма заполнялись `kinopoisk_id`, `title`, `year`, `poster_url`, `genres`.
- **Контракт API фильмов/карточек**
  - Добавить `genres` в схемы фильма в [backend/src/api/films/schemas.py](backend/src/api/films/schemas.py) и ответы в [backend/src/api/films/routes.py](backend/src/api/films/routes.py).
  - Расширить `CardCreateRequest`/`CardDetailResponse` в [backend/src/api/cards/schemas.py](backend/src/api/cards/schemas.py):
    - вход: `kinopoisk_id`, `genres`
    - выход: `film_kinopoisk_id`, `film_genres`
- **Бизнес-валидация создания карточки**
  - В [backend/src/services/cards/create_movie_card.py](backend/src/services/cards/create_movie_card.py):
    - получить `Film` по `film_id` (не только `id`),
    - проверить, что `payload.kinopoisk_id == film.kinopoisk_id`,
    - нормализовать `genres` (trim, dedup, lower-case policy),
    - при расхождении обновлять `film.genres` (или отклонять запрос — реализуем согласованный strict/soft режим, по умолчанию soft update с безопасной нормализацией).
  - В [backend/src/api/cards/routes.py](backend/src/api/cards/routes.py) прокинуть новые поля в `CreateMovieCardInput`.
- **DTO для чтения карточек**
  - Добавить `film_kinopoisk_id` и `film_genres` в:
    - [backend/src/services/cards/get_movie_card_details.py](backend/src/services/cards/get_movie_card_details.py)
    - [backend/src/services/profile/list_user_movie_cards.py](backend/src/services/profile/list_user_movie_cards.py)
    - [backend/src/api/profile/schemas.py](backend/src/api/profile/schemas.py)
- **Фронтенд**
  - Расширить типы в [frontend/src/api/profileTypes.ts](frontend/src/api/profileTypes.ts): `Film.genres`, поля карточки с `film_kinopoisk_id`, `film_genres`.
  - Обновить payload в [frontend/src/api/cardApi.ts](frontend/src/api/cardApi.ts) и сабмит в [frontend/src/pages/CreateCardPage.tsx](frontend/src/pages/CreateCardPage.tsx): отправлять `film_id`, `kinopoisk_id`, `genres`.
  - (Опционально UI) показать жанры на шаге подтверждения фильма в `CreateCardPage` как read-only.

## Проверки и тесты
- Обновить/добавить тесты в [backend/src/tests/api/test_cards_routes.py](backend/src/tests/api/test_cards_routes.py):
  - happy path с `kinopoisk_id + genres` в payload,
  - 422 при несовпадении `kinopoisk_id` с фильмом,
  - нормализация/ограничения `genres` (пустые, дубли, слишком длинные значения),
  - наличие `film_kinopoisk_id` и `film_genres` в `GET /api/cards/{id}` и `/api/users/{id}/cards`.
- Расширить тест `resolve_film` в том же файле: мок Kinopoisk payload с жанрами и проверка сохранения/отдачи.
- Прогон backend-тестов в Docker: `make backend-test` (или целевые `make backend-test-one ...`).

## Риски и совместимость
- Изменение контракта `POST /api/cards` потенциально breaking для старых клиентов; смягчить через временную опциональность новых полей на сервере и постепенный переход фронта.
- Согласовать единый формат жанров (`string[]`) на всех уровнях: Kinopoisk client -> DB -> API -> frontend.

## Порядок выполнения
1. БД/модель `Film.genres` + миграция.
2. Kinopoisk client + resolve service.
3. Схемы и route mapping (`films`, `cards`, `profile`).
4. Сервис создания карточки с валидацией согласованности.
5. Фронтенд payload и типы.
6. Тесты + прогон внутри Docker.
