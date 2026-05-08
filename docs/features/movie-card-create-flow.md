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
- `frontend/src/components/share/ShareFollowersPicker.tsx`
- `frontend/src/pages/ShareMovieCardPage.tsx`
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

## UX update: пошаговый wizard (2026-05-06)

- Экран создания карточки на `frontend/src/pages/CreateCardPage.tsx` теперь разбит на 5 нумерованных этапов.
- Этап 1: ввод ссылки Кинопоиска и запрос в `POST /api/films/resolve`.
- Этап 2: подтверждение найденного фильма (постер + название). Три кнопки без лишнего текста: **Оценить просмотр**, **К просмотру** (watchlist + переход в профиль на сегмент «К просмотру»), **Другой фильм**. Подробнее: [`watchlist.md`](./watchlist.md).
- Этап 3: оценка (1..10, шаг 0.5) и выбор контекста через цветные chips, включая блок «С кем смотрели».
- Этап 4: добавление собственных тегов (до 5).
- Этап 5: тот же выбор подписчиков, что и на экране «Поделиться» (`/cards/:id/share`): превью фильма, список подписчиков с множественным выбором, подсказка про Telegram. Кнопка **Готово** создаёт карточку; если выбраны получатели, сразу вызывается `POST /api/cards/{id}/share` (как при шаринге из карточки). При ошибке отправки после успешного создания выполняется переход на `/cards/{id}/share`, чтобы повторить отправку.
- После успешного создания (и шаринга, если был) — переход в профиль, как раньше.

Дополнительно упрощен экран Ленты (`frontend/src/pages/FeedPage.tsx`): убран устаревший текст-заглушка, оставлен лаконичный CTA для запуска wizard.

## UX update: шаг 2 — «К просмотру» без оценки (2026-05-08)

- На этапе подтверждения фильма третий сценарий: **К просмотру** — без прохождения шагов оценки и тегов; интерфейс без длинных поясняющих абзацев (смысл кнопок самодостаточен).
- После успешного добавления выполняется переход в профиль с активным сегментом «К просмотру» (`navigation state`).
- На странице фильма (`FilmDetailPage`) — кнопка **К просмотру**, если фильма ещё нет в списке.
- Продуктовая документация: [`watchlist.md`](./watchlist.md).

## UX update: шаг 5 — поделиться при создании (2026-05-08)

- Общий UI вынесен в `frontend/src/components/share/ShareFollowersPicker.tsx` (превью + список подписчиков + состояние загрузки).
- `frontend/src/pages/ShareMovieCardPage.tsx` использует тот же компонент; отправка запроса шаринга идёт через `apiJson` + тип `ShareMovieCardResponse` из `cardApi` (контракт совпадает с `shareMovieCardWithFollowers`).

## UX update: постеры в профиле и деталка карточки (2026-05-06)

- Backend получил endpoint `GET /api/cards/{card_id}` для загрузки одной карточки фильма с деталями фильма и тегами.
- В профилях (`frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/PublicProfilePage.tsx`) список карточек заменен на единый грид постеров через `frontend/src/components/profile/MoviePosterGrid.tsx`.
- Все постеры в гриде одинаковых пропорций/размеров; в ячейках показывается только постер.
- По клику на постер открывается новая страница деталки `frontend/src/pages/MovieCardDetailPage.tsx` по маршруту `/cards/:cardId`.
- На детальном экране отображаются реальные поля карточки; блок «Друзья оценили» заполняется из `GET /api/cards/{id}/following-ratings` (подписки с оценкой того же фильма, см. [`movie-card-following-ratings.md`](./movie-card-following-ratings.md)). Комментарии — рабочая фича; шаринг карточки — отдельный маршрут `/cards/:id/share`.

## UX update: rating + real comments (2026-05-06)

- Блок "Твоя оценка" на деталке переработан: теперь это одно крупное число с цветным ring/glow, зависящим от оценки.
- Блок "Лучшая оценка" удален с детальной страницы.
- Комментарии переведены из mock в рабочую фичу:
  - `GET /api/cards/{card_id}/comments`
  - `POST /api/cards/{card_id}/comments`
  - многострочный ввод до 250 символов;
  - древовидная структура комментариев с неограниченной вложенностью;
  - у каждого комментария есть автор (имя/аватар), время и ссылка на профиль автора.
