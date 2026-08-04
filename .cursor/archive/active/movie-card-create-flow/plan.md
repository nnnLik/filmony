# Plan: movie-card-create-flow

## Feature
- Slug: `movie-card-create-flow`
- Source spec: `.cursor/features/movie-card-create-flow/feature.md`

## Goal
- Реализовать production-ready создание карточки фильма: резолв фильма по ссылке Кинопоиска, создание карточки с оценкой шагом 0.5, вывод карточек в профиле.

## Step-by-Step Plan
1. Добавить backend сущности `film`, `movie_card`, `movie_card_tag` и миграцию.
2. Реализовать `POST /api/cards` + валидацию/дедупликацию/ошибки `409`.
3. Реализовать `POST /api/films/resolve` и `GET /api/films/{id}`.
4. Подключить реальный `GET /api/users/{user_id}/cards` и `cards_count`.
5. Добавить frontend страницу `/cards/new` (resolve, preview, форма карточки).
6. Интегрировать вход из ленты и отображение реальных карточек в профилях.
7. Добавить backend тесты для cards/films/profile интеграции.

## Verification Plan
- `make backend-test-one target=src/tests/api/test_cards_routes.py`
- `make backend-test-one target=src/tests/api/test_profile_routes.py`
- `cd frontend && npm run lint && npm run build`

## Iteration: wizard UX refresh (2026-05-06)
1. Упростить `FeedPage`: убрать временный текст и оставить лаконичный CTA на создание карточки.
2. Перестроить `CreateCardPage` в нумерованный wizard из 5 этапов (`URL -> confirmation -> rating/tags -> custom tags -> mock sharing`).
3. На шаге URL использовать существующий backend `POST /api/films/resolve`; ошибки парсинга показывать понятным текстом на том же экране.
4. На шаге подтверждения показать постер и имя фильма, добавить развилку «Это тот фильм?»: при «нет» вернуть к шагу 1.
5. На шаге оценки сохранить текущую шкалу 1..10 с шагом 0.5 и оформить контекстные теги цветными прямоугольными chips.
6. Финал: мок-экран про будущий sharing, кнопка `Готово`, создание карточки через `POST /api/cards`, переход в `/profile`.

## Iteration: poster grid and card details (2026-05-06)
1. Добавить backend endpoint `GET /api/cards/{card_id}` для детального просмотра карточки с film-полями и тегами.
2. Добавить backend тесты для endpoint: `401`, `404`, успешный ответ и доступ из-под другого авторизованного пользователя.
3. Заменить списки карточек в `ProfilePage` и `PublicProfilePage` на одинаковую сетку постеров фиксированного размера без текстовых подписей.
4. Добавить frontend страницу `/cards/:cardId` с загрузкой карточки по API и deep-link поддержкой.
5. Реализовать на детальном экране реальный блок данных карточки и статические mock-блоки по референсному макету.
