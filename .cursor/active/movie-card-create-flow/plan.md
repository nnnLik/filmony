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
