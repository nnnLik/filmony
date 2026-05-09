# Вкладка «Поиск» (локальный каталог)

## Назначение

В Mini App добавлена вкладка **Поиск** в нижней навигации: локальный поиск **тайтлов** (`film`) и **пользователей** (`user`), плюс блок **подсказок людей** до ввода запроса.

## API

### `GET /api/search`

- **Авторизация:** обязательна (Bearer / session cookie).
- **Параметры:** `q` (обязательно, 2–64 символа после `trim`), `limit_films`, `limit_users` (1–30, по умолчанию 15).
- **Ответ:** `{ "films": [...], "users": [...] }` — см. `SearchCatalogResponse` в `backend/src/api/search/schemas.py`.
- **Поведение:** `ILIKE` по `film.title`; по пользователю — `display_name`, `username`, `profile_slug`.

### `GET /api/search/suggestions`

- **Авторизация:** обязательна.
- **Ответ:** три непересекающихся списка (дедуп по приоритету):
  - `mutual_circle` — пересечение подписок с теми, кого смотрит текущий пользователь (`user_subscription`), без себя и без уже подписанных (до 5).
  - `popular_authors` — топ авторов по числу **новых** `movie_card` за 7 дней по `created_at` (до 5), без пользователей из первого списка.
  - `random_with_cards` — случайные пользователи с ≥1 карточкой (до 5), без уже попавших в первые два списка.

## Фронтенд

- Маршрут: `/search` внутри `AppShell`.
- `BottomNav`: третий пункт «Поиск» (иконка из `lucide-react`).
- `SearchPage`: секции подсказок, поле ввода с debounce ~320 ms, результаты, пустые состояния и CTA «Добавить карточка» → `/cards/new`.
- Клиент: `frontend/src/api/searchApi.ts`.

## Тесты

- `backend/src/tests/api/test_search_routes.py` — 401, валидация `q`, поиск, mutual/popular/random, дедуп, окно 7 дней.

## Верификация

```bash
make backend-test
cd frontend && npm run lint && npm run build
```
