# Любимые карточки (избранное)

Пользователь помечает **свои** карточки фильмов как избранные. Состояние видно в API всем (включая гостей профиля), менять избранное может только владелец. Секция «Любимое» на экранах профиля на фронтенде по продуктовому плану **не показывается**, если `favorites_count === 0`.

## Статус реализации

| Слой | Статус |
|------|--------|
| Бэкенд (модель, миграция, API, тесты) | Сделано |
| Фронтенд (сердечко, полоса «Любимое», типы) | Не сделано в данной ветке состояния репозитория |

## Данные

- Таблица `movie_card`:
  - `is_favorite` (`boolean`, по умолчанию `false`)
  - `favorite_marked_at` (`timestamptz`, nullable)
- Индекс частичный `ix_movie_card_user_favorites_order` (по `user_id`, `favorite_marked_at DESC`, `id DESC`) при `is_favorite IS TRUE`.
- Миграция: `backend/src/migrations/versions/a1b2c3d4e5f6_movie_card_favorite.py` (revision `a1b2c3d4e5f6`).

## Бизнес-правила

- **Включение:** `PATCH /api/cards/{id}` с `{"is_favorite": true}` — выставляет `is_favorite` и обновляет `favorite_marked_at` на текущий UTC (карточка поднимается вверху списка избранного).
- **Выключение:** то же с `false` — сбрасывает флаг и обнуляет `favorite_marked_at`.
- **Доступ:** патч только если `card.user_id == viewer`; иначе `403`.
- **Порядок избранного:** `GET /api/users/{user_id}/cards?favorites_only=true` — по убыванию `favorite_marked_at`, затем `id`; курсор формата `fav1.<микросекунды_эпохи>.<card_id>`.

## API

### Профиль

- `GET /api/me/profile` и `GET /api/users/{user_id}`: поле **`favorites_count`** — число карточек пользователя с `is_favorite = true`.

### Список карточек пользователя

- `GET /api/users/{user_id}/cards`
  - Query: **`favorites_only`** (`bool`, по умолчанию `false`).
  - Элемент **`MovieCardItemResponse`**: поле **`is_favorite`**.

### Карточка и лента

- `GET /api/cards/{id}` (`CardDetailResponse`): **`is_favorite`**.
- `GET /api/cards/feed`: каждый элемент — **`is_favorite`**.
- `PATCH /api/cards/{id}` (`CardUpdateRequest`): опционально **`is_favorite`**; ответ `CardResponse` содержит **`is_favorite`**.
- `POST /api/cards`: ответ `CardResponse` включает **`is_favorite`** (для новой карточки обычно `false`).

## Сервисы и схемы (ключевые файлы)

- Модель: [`backend/src/models/movie_card.py`](../backend/src/models/movie_card.py)
- Обновление: [`backend/src/services/cards/update_movie_card.py`](../backend/src/services/cards/update_movie_card.py)
- Деталка: [`backend/src/services/cards/get_movie_card_details.py`](../backend/src/services/cards/get_movie_card_details.py)
- Лента: [`backend/src/services/cards/list_movie_card_feed.py`](../backend/src/services/cards/list_movie_card_feed.py)
- Список по пользователю: [`backend/src/services/profile/list_user_movie_cards.py`](../backend/src/services/profile/list_user_movie_cards.py)
- Счётчики профиля: [`backend/src/services/profile/get_user_profile_counts.py`](../backend/src/services/profile/get_user_profile_counts.py)
- HTTP: [`backend/src/api/cards/routes.py`](../backend/src/api/cards/routes.py), [`backend/src/api/profile/users_routes.py`](../backend/src/api/profile/users_routes.py)
- Схемы: [`backend/src/api/cards/schemas.py`](../backend/src/api/cards/schemas.py), [`backend/src/api/profile/schemas.py`](../backend/src/api/profile/schemas.py)

## Тесты

- [`backend/src/tests/api/test_cards_routes.py`](../backend/src/tests/api/test_cards_routes.py): переключение `is_favorite`, запрет для чужой карточки, поле в `GET` карточки.
- [`backend/src/tests/api/test_profile_routes.py`](../backend/src/tests/api/test_profile_routes.py): `favorites_count`, список `favorites_only` и порядок.

## Фронтенд (план доработки)

- Типы и клиенты: `is_favorite` на карточках, `favorites_count` на профиле; `PATCH` с `is_favorite`; `getUserCards(..., favoritesOnly: true)`.
- UI: кнопка-сердце на своих карточках (лента, деталка, сетка профиля); горизонтальная полоса «Любимое» при `favorites_count > 0`.

## Проверка

После применения миграций в окружении Docker: `make migrate`, затем `make backend-test` (см. корневой `Makefile` и `.cursor/tech.md`).
