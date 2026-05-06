# Implementation Plan

## Feature
- Slug: `movie-card-comments-telegram-like`
- Source spec: `.cursor/features/movie-card-comments-telegram-like/feature.md`

## Goal
- Перевести комментарии карточки фильма на плоскую Telegram-like модель с parent preview и переходом к родителю.

## Assumptions
- Хранение комментариев в БД остается прежним, включая `parent_comment_id`.
- Endpoint `GET /api/cards/{card_id}/comments/{comment_id}/replies` можно оставить для совместимости, но UI не будет на него опираться.

## Step-by-Step Plan
1. Подготовить feature артефакты и журнал прогресса.
2. Перевести backend list comments endpoint на плоский режим и адаптировать API тесты.
3. Переписать frontend комментарии в `MovieCardDetailPage` на плоский список с reply preview и parent jump + autoload.
4. Убрать thread-страницу из роутинга и прекратить ее использование.
5. Прогнать проверки и оформить итоговые docs/memory записи.

## Files Expected To Change
- `backend/src/services/cards/list_movie_card_comments.py`
- `backend/src/api/cards/routes.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/MovieCardCommentThreadPage.tsx`
- `frontend/src/routes.tsx`
- `.cursor/features/movie-card-comments-telegram-like/feature.md`
- `.cursor/active/movie-card-comments-telegram-like/{plan.md,progress.md,result.md}`
- `docs/features/movie-card-comments-telegram-like.md`
- `.cursor/memory/logs/*.md`

## Verification Plan
- Commands to run:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `npm run lint` / `npm run test` / `npm run build` в frontend (по доступности скриптов).
- Manual checks:
  - Проверить отображение плоского списка комментариев.
  - Проверить reply preview и переход к родителю.
- **Backend tests:** обновить `backend/src/tests/api/test_cards_routes.py` для полного покрытия новой выдачи списка, пагинации и валидации parent-связей.

## Risks And Mitigations
- Risk: родительский комментарий может отсутствовать в загруженном диапазоне и не находиться за разумное число запросов.
  - Mitigation: ограниченный цикл автодогрузки до исчерпания `next_cursor`, явное сообщение пользователю при отсутствии.
- Risk: регрессия существующих consumer'ов replies endpoint.
  - Mitigation: сохранить endpoint и изменить только основной list контракт для root/reply выдачи.
