# Вкладка «Поиск» (локальный каталог + люди)

## Назначение

В Mini App есть вкладка **Поиск** в нижней навигации. Она ищет только по локальным данным Filmony: карточки пользователей и профили людей. Внешние провайдеры в этом сценарии не используются.

Основной список ответа `GET /api/search` — **`cards`**. Поле **`films`** оставлено как legacy alias для совместимости: если клиент ещё ждёт старый формат, он продолжит работать, но новая выдача уже строится вокруг карточек.

## API

### `GET /api/search`

- **Авторизация:** обязательна.
- **Параметры:** `q` (обязательно, 2–64 символа после `trim`), `limit_cards`, `limit_users`, а для совместимости ещё `limit_films`.
- **Ответ:** `{ "cards": [...], "films": [...], "users": [...] }`.
- **Карточки:** поиск по локальным карточкам, включая manual cards; результат показывает название, описание, автора, год, рейтинг и постер.
- **Пользователи:** поиск по `display_name`, `username`, `profile_slug`.

### `GET /api/search/suggestions`

- **Авторизация:** обязательна.
- **Ответ:** три непересекающихся списка с дедупликацией по приоритету: `mutual_circle` → `popular_authors` → `random_with_cards`.

## Фронтенд

- Маршрут: `/search`.
- Основная выдача карточек открывается по **`/cards/:cardId`**.
- Если сервер ещё отдаёт только legacy `films`, клиент использует fallback на **`/films/:filmId`**.
- Страница показывает подсказки людей, debounce в поле поиска и пустые состояния.

## Тесты

- `backend/src/tests/services/test_search_catalog_cards_service.py`
- `backend/src/tests/api/test_search_routes.py`

## Верификация

```bash
docker compose -f docker-compose.yml exec -T backend pytest -q
cd frontend && npm run lint && npm run build
```
