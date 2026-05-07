# Оценки подписок на том же фильме («Друзья оценили»)

## Цель

На экране деталки карточки (`/cards/:cardId`) показывать, как **люди, на которых подписан текущий пользователь**, оценили **тот же фильм** (тот же `film_id` в БД, он же канон Кинопоиска через карточки). Список короткий, отсортирован по убыванию оценки, с аватаром и именем.

## Правила отбора

- Источник совпадения фильма: поле `movie_card.film_id` у **открытой** карточки-якоря и у карточек кандидатов.
- В списке только пользователи, на которых зритель **подписан** (`user_subscription`: `follower_user_id` = зритель, `following_user_id` = автор карточки кандидата).
- Исключаются: **зритель** (своя карточка на этот фильм не дублируется в виджете) и **автор открытой карточки** (его оценка уже показана крупно на экране).
- Максимум **5** записей; сортировка: `rating DESC`, затем `movie_card.id DESC` для стабильности.

## API

| Метод | Путь | Auth |
|--------|------|------|
| `GET` | `/api/cards/{card_id}/following-ratings` | Cookie-сессия (как и деталка карточки) |

Ответ: `{ "items": [ { "user_id", "profile_slug", "username", "first_name", "last_name", "photo_url", "display_name", "rating" }, ... ] }`.

Ошибки: `404`, если карточки-якоря нет.

## Backend

- Сервис: `backend/src/services/cards/list_following_ratings_for_movie_card.py` — `ListFollowingRatingsForMovieCardService.execute(viewer_user_id, anchor_card_id)`.
- Роут: `backend/src/api/cards/routes.py` (маршрут объявлен **выше** `GET /cards/{card_id}`, чтобы не пересекаться с общим паттерном).
- Схемы: `FollowingRatingEntryResponse`, `FollowingRatingsListResponse` в `backend/src/api/cards/schemas.py`.

## Frontend

- Клиент: `getFollowingRatingsForCard` в `frontend/src/api/cardApi.ts`.
- Типы: `FollowingRatingEntry`, `FollowingRatingsResponse` в `frontend/src/api/profileTypes.ts`.
- UI: блок «Друзья оценили» на `frontend/src/pages/MovieCardDetailPage.tsx` — загрузка после открытия страницы, строки с `Avatar`, именем (`displayNameFromProfile`), оценкой с цветом по тем же порогам, что и основная оценка (`ratingPalette`), ссылка на `/u/:userId`.

## Тесты

- `backend/src/tests/api/test_following_ratings_for_movie_card.py` — сортировка и состав списка при подписках; `404` для несуществующей карточки.

## Проверка (выполнить локально в Docker)

Из корня репозитория, при поднятом compose:

```bash
make backend-test-one target=src/tests/api/test_following_ratings_for_movie_card.py
```

Полный регресс бэкенда:

```bash
make backend-test
```

Сборка фронта:

```bash
cd frontend && npm run build
```

## Ограничения и дальше

- Не показываются пользователи без подписки зрителя, даже если оценили фильм.
- Лимит 5 зафиксирован в константе `FOLLOWING_RATINGS_TOP_LIMIT`; при необходимости вынести в query-параметр в отдельной задаче.
