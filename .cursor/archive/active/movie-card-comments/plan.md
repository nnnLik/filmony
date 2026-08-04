# Plan: movie-card-comments

## Feature
- Slug: `movie-card-comments`
- Source spec: `.cursor/features/movie-card-comments/feature.md`

## Goal
- Внедрить backend API комментариев под карточкой фильма: публичное чтение, auth-only создание, ответы любой глубины.

## Steps
1. Обновить модель и миграции комментариев под нужный контракт чтения/пагинации.
2. Реализовать сервисы создания комментария и листинга веток (root/replies) с cursor pagination.
3. Обновить `cards` API схемы и endpoints (`GET comments`, `GET replies`, `POST comment`).
4. Добавить/обновить API тесты для auth, валидации, parent consistency и пагинации.
5. Запустить backend проверки и зафиксировать результат в документации/логах.

## Verification Plan
- `make backend-test-one target=src/tests/api/test_cards_routes.py`
- `make backend-test`
