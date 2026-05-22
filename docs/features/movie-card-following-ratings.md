# Оценки подписок на том же тайтле («Друзья оценили»)

В UI блок может называться «Друзья оценили»; по данным это пользователи, **на которых подписан зритель** (following), с отдельной карточкой на **тот же тайтл**.

## Цель

На экране деталки карточки (`/cards/:cardId`) показывать, как **люди, на которых подписан текущий пользователь**, оценили **ту же тему**:

- **Фильм / сериал (Кинопоиск):** совпадение по `film_id` в БД.
- **Игра (RAWG и др. каталог без `film_id`):** совпадение по **`catalog_item_id`**, когда у якорной карточки `film_id` пустой.

Список короткий, отсортирован по убыванию оценки, с аватаром и именем.

## Правила отбора

- Источник совпадения:
  - если у якоря задан `film_id` — сравнение по `movie_card.film_id`;
  - иначе, если задан `catalog_item_id` — сравнение по `movie_card.catalog_item_id`;
  - если ни того ни другого — список пуст.
- В списке только пользователи, на которых зритель **подписан** (`user_subscription`: `follower_user_id` = зритель, `following_user_id` = автор карточки кандидата).
- Исключаются: **зритель** (своя карточка на этот тайтл не дублируется в виджете; при открытии чужой карточки она попадает в `viewer_rating`) и **автор открытой карточки** (его оценка уже показана крупно на экране).
- Максимум **5** записей; сортировка: `rating DESC`, затем `movie_card.id DESC` для стабильности.

## Создание карточки «по мотивам» (remix)

Если пользователь открывает `/cards/new?fromCard=<id>` с чужой **RAWG**-карточкой (`provider: rawg`, есть `catalog_item_id`), клиент должен сохранять **каталожную привязку** и отправлять создание через путь с `catalog_item_id`, а не как ручную карточку без каталога. Иначе новая карточка теряет общий якорь с друзьями, и блок «Друзья оценили» перестаёт находить совпадения.

## API

| Метод | Путь | Auth |
|--------|------|------|
| `GET` | `/api/cards/{card_id}/following-ratings` | Cookie-сессия (как и деталка карточки) |

Ответ: `{ "viewer_rating": … | null, "items": [ { "user_id", "movie_card_id", "profile_slug", …, "rating" }, ... ] }`.

Ошибки: `404`, если карточки-якоря нет.

## Backend

- Сервис: `backend/src/services/cards/list_following_ratings_for_user_card.py` — `ListFollowingRatingsForUserCardService.execute(viewer_user_id, anchor_card_id)`.
- Роут: `backend/src/api/cards/routes.py` (маршрут объявлен **выше** `GET /cards/{card_id}`, чтобы не пересекаться с общим паттерном).
- Схемы: `FollowingRatingEntryResponse`, `FollowingRatingsListResponse` в `backend/src/api/cards/schemas.py`.

## Frontend

- Клиент: `getFollowingRatingsForCard` в `frontend/src/api/cardApi.ts`.
- Типы: `FollowingRatingEntry`, `FollowingRatingsResponse` в `frontend/src/api/profileTypes.ts`.
- UI: блок «Друзья оценили» на `frontend/src/pages/MovieCardDetailPage.tsx` — загрузка после открытия страницы, строки с `Avatar`, именем (`displayNameFromProfile`), оценкой с цветом по тем же порогам, что и основная оценка (`ratingPalette`), ссылка на `/u/:userId`.
- Мастер создания: `frontend/src/pages/CreateCardPage.tsx` — ветка `fromCard` для RAWG с `catalog_item_id` задаёт привязку `catalog_game`, чтобы не терять общий `catalog_item_id`.

## Тесты

- `backend/src/tests/api/test_following_ratings_for_movie_card.py` — Кинопоиск: сортировка и состав списка при подписках; `viewer_rating`; `404` для несуществующей карточки. **RAWG:** те же сценарии при общем `catalog_item_id` и `film_id = null`.

## Проверка (выполнить локально в Docker)

Из корня репозитория, при поднятом compose (при необходимости без TTY):

```bash
docker exec -w /opt/app filmony-backend pytest src/tests/api/test_following_ratings_for_movie_card.py -v
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

- Не показываются пользователи без подписки зрителя, даже если оценили тот же тайтл.
- Лимит 5 зафиксирован в константе `FOLLOWING_RATINGS_TOP_LIMIT`; при необходимости вынести в query-параметр в отдельной задаче.
