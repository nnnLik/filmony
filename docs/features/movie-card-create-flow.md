# Feature: создание карточки фильма (`movie-card-create-flow`)

Фича объединяет требования из [004](../../.cursor/features/004-kinopoisk-movie-by-link.md) и [005](../../.cursor/features/005-movie-rating-with-tags.md): от ссылки Кинопоиска до сохраненной карточки в профиле.

## Что реализовано

- Backend:
  - `POST /api/films/resolve` — резолв URL Кинопоиска в канонический фильм.
  - `GET /api/films/{film_id}` — получение фильма по id.
  - `POST /api/cards` — создание карточки фильма.
  - Реальный `GET /api/users/{user_id}/cards` и подсчет `cards_count`.
- Frontend:
  - Маршрут `/cards/new`.
  - Поток `URL -> preview -> create card`.
  - Оценка `1..10` с шагом `0.5`.
  - Контекстные теги (`company`, `mood_before`, `mood_after`) и до 5 custom tags.
  - Точка входа из ленты (`/` -> `Добавить фильм`).

## Бизнес-правила

- Одна карточка на пользователя и фильм (`(user_id, film_id)` уникальны).
- Повторный `POST /api/cards` на ту же пару возвращает `409`.
- Оценка валидируется в диапазоне `1..10` с кратностью `0.5`.
- Пользовательские теги:
  - не более 5,
  - trim,
  - case-insensitive дедупликация.

## API (v1)

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/films/resolve` | body `{ "url": "https://www.kinopoisk.ru/film/..." }` |
| `GET` | `/api/films/{film_id}` | получить фильм для preview/detail |
| `POST` | `/api/cards` | создать карточку для текущего пользователя |
| `GET` | `/api/users/{user_id}/cards` | paginated список карточек профиля |

## Основные backend-файлы

- `backend/src/models/film.py`
- `backend/src/models/movie_card.py`
- `backend/src/models/movie_card_tag.py`
- `backend/src/models/movie_card_enums.py`
- `backend/src/services/cards/create_movie_card.py`
- `backend/src/services/kinopoisk/*`
- `backend/src/api/cards/routes.py`
- `backend/src/api/films/routes.py`
- `backend/src/tests/api/test_cards_routes.py`

## Основные frontend-файлы

- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/api/cardApi.ts`
- `frontend/src/routes.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Проверка

Рекомендованные команды:

- `make backend-test-one target=src/tests/api/test_cards_routes.py`
- `make backend-test`
- `cd frontend && npm run lint && npm run build`
