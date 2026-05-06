# Implementation Plan

## Feature
- Slug: `movie-card-edit-delete`
- Source spec: `.cursor/features/movie-card-edit-delete/feature.md`

## Goal
- Добавить owner-only редактирование и удаление карточек фильма через backend API и frontend UI.

## Step-by-Step Plan
1. Добавить backend контракты и сервисы для `PATCH /api/cards/{card_id}` и `DELETE /api/cards/{card_id}` с policy `403` для чужих карточек.
2. Расширить backend тесты `cards` API на happy-path, auth, permission и validation сценарии.
3. Расширить frontend API слой (`updateMovieCard`, `deleteMovieCard`).
4. Добавить UI-меню действий на detail-экране и отдельный экран редактирования карточки.
5. Добавить confirm flow удаления, инвалидацию профиля в session cache и корректную навигацию.
6. Обновить feature-артефакты и action-log, зафиксировать результаты верификации.

## Files Expected To Change
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/services/cards/update_movie_card.py`
- `backend/src/services/cards/delete_movie_card.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/EditMovieCardPage.tsx`
- `frontend/src/routes.tsx`

## Verification Plan
- `make backend-test-one target=src/tests/api/test_cards_routes.py` (Docker).
- `cd frontend && npm run lint` (или локальный lint-эквивалент в CI).
- Ручной smoke test:
  - owner: detail -> menu -> edit/save;
  - owner: detail -> menu -> delete/confirm;
  - non-owner: отсутствие owner actions и backend `403` в API тестах.
